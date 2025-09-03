import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from src.models.journal_sentiments import JournalSentiments

logger = logging.getLogger(__name__)


def create_or_update_sentiment(
    db: Session,
    journal_id: int,
    sentiment_data: dict[str, Any],
    force_update: bool = False,
) -> JournalSentiments:
    """Create or update sentiment analysis for a journal entry."""
    try:
        model_version = sentiment_data["ml_model_version"]

        # Check for existing sentiment analysis
        existing = (
            db.query(JournalSentiments)
            .filter(
                and_(
                    JournalSentiments.journal_id == journal_id,
                    JournalSentiments.ml_model_version == model_version,
                )
            )
            .first()
        )

        if existing:
            if force_update:
                # Update existing record
                existing.sentiment = sentiment_data["sentiment"]
                existing.confidence = sentiment_data["confidence"]
                existing.confidence_level = sentiment_data["confidence_level"]
                existing.is_reliable = sentiment_data["is_reliable"]
                existing.all_scores = sentiment_data.get("all_scores")
                existing.created_at = func.now()
                sentiment_record = existing
                logger.info(
                    f"Updated sentiment for journal {journal_id}, model {model_version}"
                )
            else:
                # Return existing without updating
                logger.info(
                    f"Sentiment already exists for journal {journal_id}, "
                    f"model {model_version}"
                )
                return existing
        else:
            # Create new record
            sentiment_record = JournalSentiments(
                journal_id=journal_id,
                sentiment=sentiment_data["sentiment"],
                confidence=sentiment_data["confidence"],
                confidence_level=sentiment_data["confidence_level"],
                is_reliable=sentiment_data["is_reliable"],
                ml_model_version=model_version,
                all_scores=sentiment_data.get("all_scores"),
            )
            db.add(sentiment_record)
            logger.info(
                f"Created new sentiment for journal {journal_id}, model {model_version}"
            )

        db.commit()
        db.refresh(sentiment_record)
        return sentiment_record

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating/updating sentiment for journal {journal_id}: {e}")
        raise


def get_sentiment_by_journal_id(
    db: Session, journal_id: int, model_version: str | None = None
) -> JournalSentiments | None:
    """Get sentiment analysis for a specific journal entry."""
    try:
        query = db.query(JournalSentiments).filter(
            JournalSentiments.journal_id == journal_id
        )

        if model_version:
            query = query.filter(JournalSentiments.ml_model_version == model_version)

        # Get the most recent analysis
        sentiment = query.order_by(desc(JournalSentiments.created_at)).first()

        if sentiment:
            logger.debug(f"Retrieved sentiment for journal {journal_id}")
        else:
            logger.debug(f"No sentiment found for journal {journal_id}")

        return sentiment

    except Exception as e:
        logger.error(f"Error retrieving sentiment for journal {journal_id}: {e}")
        raise


def get_sentiments_by_journal_ids(
    db: Session, journal_ids: list[int], reliable_only: bool = False
) -> list[JournalSentiments]:
    """Get sentiment analysis for multiple journal entries."""
    try:
        query = db.query(JournalSentiments).filter(
            JournalSentiments.journal_id.in_(journal_ids)
        )

        if reliable_only:
            query = query.filter(JournalSentiments.is_reliable is True)

        sentiments = query.order_by(desc(JournalSentiments.created_at)).all()

        logger.info(
            f"Retrieved {len(sentiments)} sentiment records for "
            f"{len(journal_ids)} journals"
        )
        return sentiments

    except Exception as e:
        logger.error(f"Error retrieving sentiments for journals {journal_ids}: {e}")
        raise


def get_sentiment_trends(
    db: Session,
    days_back: int = 30,
    group_by: str = "week",
    reliable_only: bool = True,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    """Get sentiment trends over time."""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Build query
        query = db.query(JournalSentiments).filter(
            JournalSentiments.created_at >= start_date
        )

        if reliable_only:
            query = query.filter(JournalSentiments.is_reliable is True)

        # Add user filter if provided (assuming journals table has user_id)
        # if user_id:
        #     query = query.join(Journal).filter(Journal.user_id == user_id)

        # Group by time period
        if group_by == "day":
            time_group = func.date_trunc("day", JournalSentiments.created_at)
        elif group_by == "week":
            time_group = func.date_trunc("week", JournalSentiments.created_at)
        elif group_by == "month":
            time_group = func.date_trunc("month", JournalSentiments.created_at)
        else:
            raise ValueError("group_by must be 'day', 'week', or 'month'")

        # Execute aggregation query
        results = (
            db.query(
                time_group.label("period"),
                JournalSentiments.sentiment,
                func.count().label("count"),
                func.avg(JournalSentiments.confidence).label("avg_confidence"),
            )
            .filter(JournalSentiments.created_at >= start_date)
            .group_by(time_group, JournalSentiments.sentiment)
            .order_by(desc(time_group))
            .all()
        )

        # Transform results into response format
        trends_dict = {}
        for period, sentiment, count, avg_conf in results:
            period_str = period.strftime("%Y-%m-%d")

            if period_str not in trends_dict:
                trends_dict[period_str] = {
                    "period": period_str,
                    "sentiment_counts": {
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0,
                        "uncertain": 0,
                    },
                    "avg_confidence": 0,
                    "total_entries": 0,
                }

            trends_dict[period_str]["sentiment_counts"][sentiment] = count
            trends_dict[period_str]["total_entries"] += count
            trends_dict[period_str]["avg_confidence"] = float(avg_conf or 0)

        # Determine dominant sentiment for each period
        trends = []
        for period_data in trends_dict.values():
            sentiment_counts = period_data["sentiment_counts"]
            dominant = (
                max(sentiment_counts.items(), key=lambda x: x[1])[0]
                if any(sentiment_counts.values())
                else "neutral"
            )

            trends.append(
                {
                    "period": period_data["period"],
                    "sentiment_counts": sentiment_counts,
                    "avg_confidence": period_data["avg_confidence"],
                    "total_entries": period_data["total_entries"],
                    "dominant_sentiment": dominant,
                }
            )

        logger.info(f"Retrieved sentiment trends for {len(trends)} periods")
        return trends

    except Exception as e:
        logger.error(f"Error retrieving sentiment trends: {e}")
        raise


def get_sentiment_stats(
    db: Session, days_back: int | None = None, user_id: int | None = None
) -> dict[str, Any]:
    """Get overall sentiment analysis statistics."""
    try:
        # Build base query
        query = db.query(JournalSentiments)

        # Add date filter if provided
        if days_back:
            start_date = datetime.now() - timedelta(days=days_back)
            query = query.filter(JournalSentiments.created_at >= start_date)

        # Add user filter if provided (assuming journals table has user_id)
        # if user_id:
        #     query = query.join(Journal).filter(Journal.user_id == user_id)

        # Get all records
        all_sentiments = query.all()

        if not all_sentiments:
            logger.warning("No sentiment analysis data found for statistics")
            return {
                "total_analyzed": 0,
                "reliable_count": 0,
                "reliability_rate": 0.0,
                "sentiment_distribution": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "uncertain": 0,
                },
                "avg_confidence": 0.0,
                "latest_model_version": None,
            }

        # Calculate statistics
        total_analyzed = len(all_sentiments)
        reliable_sentiments = [s for s in all_sentiments if s.is_reliable]
        reliable_count = len(reliable_sentiments)
        reliability_rate = reliable_count / total_analyzed if total_analyzed > 0 else 0

        # Sentiment distribution
        sentiment_distribution = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "uncertain": 0,
        }
        total_confidence = 0

        for sentiment in all_sentiments:
            sentiment_distribution[sentiment.sentiment] = (
                sentiment_distribution.get(sentiment.sentiment, 0) + 1
            )
            total_confidence += float(sentiment.confidence)

        avg_confidence = total_confidence / total_analyzed if total_analyzed > 0 else 0

        # Get latest model version
        latest_sentiment = max(all_sentiments, key=lambda s: s.created_at)
        latest_model_version = latest_sentiment.ml_model_version

        stats = {
            "total_analyzed": total_analyzed,
            "reliable_count": reliable_count,
            "reliability_rate": reliability_rate,
            "sentiment_distribution": sentiment_distribution,
            "avg_confidence": avg_confidence,
            "latest_model_version": latest_model_version,
        }

        logger.info(f"Generated sentiment statistics for {total_analyzed} records")
        return stats

    except Exception as e:
        logger.error(f"Error generating sentiment statistics: {e}")
        raise


def get_recent_sentiments(
    db: Session,
    limit: int = 10,
    reliable_only: bool = True,
    user_id: int | None = None,
) -> list[JournalSentiments]:
    """Get most recent sentiment analyses."""
    try:
        query = db.query(JournalSentiments)

        if reliable_only:
            query = query.filter(JournalSentiments.is_reliable is True)

        # Add user filter if provided (assuming journals table has user_id)
        # if user_id:
        #     query = query.join(Journal).filter(Journal.user_id == user_id)

        sentiments = (
            query.order_by(desc(JournalSentiments.created_at)).limit(limit).all()
        )

        logger.info(f"Retrieved {len(sentiments)} recent sentiment records")
        return sentiments

    except Exception as e:
        logger.error(f"Error retrieving recent sentiments: {e}")
        raise


def bulk_create_sentiments(
    db: Session, sentiment_data_list: list[tuple[int, dict[str, Any]]]
) -> list[JournalSentiments]:
    """Bulk create sentiment records for multiple journal entries."""
    try:
        sentiment_records = []

        for journal_id, sentiment_data in sentiment_data_list:
            sentiment_record = JournalSentiments(
                journal_id=journal_id,
                sentiment=sentiment_data["sentiment"],
                confidence=sentiment_data["confidence"],
                confidence_level=sentiment_data["confidence_level"],
                is_reliable=sentiment_data["is_reliable"],
                ml_model_version=sentiment_data["ml_model_version"],
                all_scores=sentiment_data.get("all_scores"),
            )
            db.add(sentiment_record)
            sentiment_records.append(sentiment_record)

        db.commit()

        for record in sentiment_records:
            db.refresh(record)

        logger.info(f"Bulk created {len(sentiment_records)} sentiment records")
        return sentiment_records

    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk creating sentiment records: {e}")
        raise


def delete_sentiment(
    db: Session, journal_id: int, model_version: str | None = None
) -> int:
    """Delete sentiment analysis for a journal entry."""
    try:
        query = db.query(JournalSentiments).filter(
            JournalSentiments.journal_id == journal_id
        )

        if model_version:
            query = query.filter(JournalSentiments.ml_model_version == model_version)

        deleted_count = query.delete()
        db.commit()

        logger.info(
            f"Deleted {deleted_count} sentiment record(s) for journal {journal_id}"
        )
        return deleted_count

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting sentiment for journal {journal_id}: {e}")
        raise
