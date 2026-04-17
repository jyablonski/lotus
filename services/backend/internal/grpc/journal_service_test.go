package grpc_test

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func int32Ptr(v int32) *int32 { return &v }

func journalPgUUID(u uuid.UUID) pgtype.UUID { return pgtype.UUID{Bytes: u, Valid: true} }

func journalPgTS(t time.Time) pgtype.Timestamp { return pgtype.Timestamp{Time: t, Valid: true} }

func journalTestCtx(dbMock db.Querier, httpMock inject.HTTPDoer) context.Context {
	ctx := context.Background()
	ctx = inject.WithDB(ctx, dbMock)
	ctx = inject.WithLogger(ctx, newTestLogger())
	ctx = inject.WithHTTPClient(ctx, httpMock)
	ctx = inject.WithAnalyzerURL(ctx, "http://localhost:8083")
	return ctx
}

func noopHTTPClient() *mocks.HTTPDoerMock {
	return &mocks.HTTPDoerMock{
		DoFunc: func(req *http.Request) (*http.Response, error) {
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(bytes.NewBufferString(`{"success": true}`)),
			}, nil
		},
	}
}

func TestJournalServer_CreateJournal_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	req := &pb.CreateJournalRequest{
		UserId:      "invalid-uuid",
		JournalText: "Test journal",
		UserMood:    "5",
	}
	resp, err := server.CreateJournal(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestJournalServer_CreateJournal_InvalidMoodScore(t *testing.T) {
	userID := uuid.New()
	server := &internalgrpc.JournalServer{}
	req := &pb.CreateJournalRequest{
		UserId:      userID.String(),
		JournalText: "Test journal",
		UserMood:    "not-a-number",
	}
	resp, err := server.CreateJournal(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidMoodScore)
}

func TestJournalServer_CreateJournal_MoodScoreOutOfRange(t *testing.T) {
	userID := uuid.New()
	server := &internalgrpc.JournalServer{}

	for _, mood := range []string{"0", "11", "-1", "99"} {
		req := &pb.CreateJournalRequest{
			UserId:      userID.String(),
			JournalText: "Test",
			UserMood:    mood,
		}
		resp, err := server.CreateJournal(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
		require.Error(t, err, "mood %q should be rejected", mood)
		require.Nil(t, resp)
		assert.ErrorIs(t, err, internalgrpc.ErrInvalidMoodScore)
	}
}

func TestJournalServer_GetJournals_Success(t *testing.T) {
	userID := uuid.New()
	now := time.Now()

	journals := []db.SourceJournal{
		{
			ID:          1,
			UserID:      journalPgUUID(userID),
			JournalText: "First journal entry",
			MoodScore:   int32Ptr(7),
			CreatedAt:   journalPgTS(now),
			ModifiedAt:  journalPgTS(now),
		},
		{
			ID:          2,
			UserID:      journalPgUUID(userID),
			JournalText: "Second journal entry",
			MoodScore:   int32Ptr(8),
			CreatedAt:   journalPgTS(now.Add(-time.Hour)),
			ModifiedAt:  journalPgTS(now.Add(-time.Hour)),
		},
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			assert.Equal(t, journalPgUUID(userID), uid)
			return 2, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, journalPgUUID(userID), arg.UserID)
			return journals, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  10,
		Offset: 0,
	}

	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.Journals, 2)
	assert.Equal(t, int64(2), resp.TotalCount)
	assert.False(t, resp.HasMore)

	assert.Equal(t, "1", resp.Journals[0].JournalId)
	assert.Equal(t, "First journal entry", resp.Journals[0].JournalText)
	assert.Equal(t, "7", resp.Journals[0].UserMood)
}

func TestJournalServer_GetJournals_WithTopics(t *testing.T) {
	userID := uuid.New()
	now := time.Now()
	journals := []db.SourceJournal{
		{ID: 1, UserID: journalPgUUID(userID), JournalText: "Entry one", MoodScore: int32Ptr(5), CreatedAt: journalPgTS(now), ModifiedAt: journalPgTS(now)},
		{ID: 2, UserID: journalPgUUID(userID), JournalText: "Entry two", MoodScore: int32Ptr(6), CreatedAt: journalPgTS(now), ModifiedAt: journalPgTS(now)},
	}
	topics := []db.GetTopicsByJournalIdsRow{
		{JournalID: 1, TopicName: "productivity"},
		{JournalID: 1, TopicName: "goals"},
		{JournalID: 2, TopicName: "reflection"},
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 2, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			return journals, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			assert.ElementsMatch(t, []int32{1, 2}, ids)
			return topics, nil
		},
	}

	resp, err := (&internalgrpc.JournalServer{}).GetJournals(
		journalTestCtx(mockQuerier, noopHTTPClient()),
		&pb.GetJournalsRequest{UserId: userID.String(), Limit: 10, Offset: 0},
	)
	require.NoError(t, err)
	require.Len(t, resp.Journals, 2)
	assert.Equal(t, []string{"productivity", "goals"}, resp.Journals[0].TopicNames)
	assert.Equal(t, []string{"reflection"}, resp.Journals[1].TopicNames)
}

func TestJournalServer_GetJournals_WithPagination(t *testing.T) {
	userID := uuid.New()
	now := time.Now()

	// Return exactly 10 journals (the limit) to trigger hasMore
	journals := make([]db.SourceJournal, 10)
	for i := 0; i < 10; i++ {
		journals[i] = db.SourceJournal{
			ID:          int32(i + 1),
			UserID:      journalPgUUID(userID),
			JournalText: "Journal entry",
			MoodScore:   int32Ptr(5),
			CreatedAt:   journalPgTS(now),
			ModifiedAt:  journalPgTS(now),
		}
	}

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 25, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, int32(10), arg.Limit)
			assert.Equal(t, int32(0), arg.Offset)
			return journals, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  10,
		Offset: 0,
	}

	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.Journals, 10)
	assert.Equal(t, int64(25), resp.TotalCount)
	assert.True(t, resp.HasMore)
}

func TestJournalServer_GetJournals_DefaultLimit(t *testing.T) {
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 0, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, int32(50), arg.Limit)
			return []db.SourceJournal{}, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  0,
		Offset: 0,
	}

	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
}

func TestJournalServer_GetJournals_MaxLimit(t *testing.T) {
	userID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		GetJournalCountByUserIdFunc: func(ctx context.Context, uid pgtype.UUID) (int64, error) {
			return 0, nil
		},
		GetJournalsByUserIdPaginatedFunc: func(ctx context.Context, arg db.GetJournalsByUserIdPaginatedParams) ([]db.SourceJournal, error) {
			assert.Equal(t, int32(100), arg.Limit)
			return []db.SourceJournal{}, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return nil, nil
		},
	}

	mockHTTPClient := noopHTTPClient()
	server := &internalgrpc.JournalServer{}

	req := &pb.GetJournalsRequest{
		UserId: userID.String(),
		Limit:  500,
		Offset: 0,
	}

	resp, err := server.GetJournals(journalTestCtx(mockQuerier, mockHTTPClient), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
}

func TestJournalServer_TriggerJournalAnalysis_Success(t *testing.T) {
	userID := uuid.New()
	journalID := int32(123)

	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			assert.Equal(t, journalID, id)
			return db.SourceJournal{
				ID:          journalID,
				UserID:      journalPgUUID(userID),
				JournalText: "Test journal",
				CreatedAt:   journalPgTS(time.Now()),
				ModifiedAt:  journalPgTS(time.Now()),
			}, nil
		},
	}

	ctx := withRiverDeps(journalTestCtx(mockQuerier, noopHTTPClient()))
	resp, err := (&internalgrpc.JournalServer{}).TriggerJournalAnalysis(ctx, &pb.TriggerAnalysisRequest{JournalId: "123"})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.True(t, resp.Success)
	assert.Equal(t, "Analysis triggered successfully", resp.Message)
	assert.Len(t, mockQuerier.GetJournalByIdCalls(), 1)
}

func TestJournalServer_TriggerJournalAnalysis_JournalNotFound(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return db.SourceJournal{}, pgx.ErrNoRows
		},
	}

	ctx := withRiverDeps(journalTestCtx(mockQuerier, noopHTTPClient()))
	resp, err := (&internalgrpc.JournalServer{}).TriggerJournalAnalysis(ctx, &pb.TriggerAnalysisRequest{JournalId: "999"})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrJournalNotFound)
}

func TestJournalServer_TriggerJournalAnalysis_InvalidJournalId(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{}
	mockHTTPClient := noopHTTPClient()

	server := &internalgrpc.JournalServer{}

	req := &pb.TriggerAnalysisRequest{
		JournalId: "not-a-number",
	}

	resp, err := server.TriggerJournalAnalysis(journalTestCtx(mockQuerier, mockHTTPClient), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidJournalID)
}

func TestJournalServer_DeleteJournal_Success(t *testing.T) {
	userID := uuid.New()
	j := db.SourceJournal{
		ID:          1,
		UserID:      journalPgUUID(userID),
		JournalText: "x",
		MoodScore:   int32Ptr(7),
		CreatedAt:   journalPgTS(time.Now()),
		ModifiedAt:  journalPgTS(time.Now()),
	}
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return j, nil
		},
		DeleteJournalForUserFunc: func(ctx context.Context, arg db.DeleteJournalForUserParams) (int64, error) {
			assert.Equal(t, int32(1), arg.ID)
			assert.Equal(t, journalPgUUID(userID), arg.UserID)
			return 1, nil
		},
	}
	srv := &internalgrpc.JournalServer{}
	resp, err := srv.DeleteJournal(journalTestCtx(mockQuerier, noopHTTPClient()), &pb.DeleteJournalRequest{
		JournalId: "1",
		UserId:    userID.String(),
	})
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.True(t, resp.Success)
}

func TestJournalServer_GetJournal_Success(t *testing.T) {
	userID := uuid.New()
	now := time.Now()
	j := db.SourceJournal{
		ID:          7,
		UserID:      journalPgUUID(userID),
		JournalText: "Full text",
		MoodScore:   int32Ptr(5),
		CreatedAt:   journalPgTS(now),
		ModifiedAt:  journalPgTS(now),
	}
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			assert.Equal(t, int32(7), id)
			return j, nil
		},
		GetTopicsByJournalIdsFunc: func(ctx context.Context, ids []int32) ([]db.GetTopicsByJournalIdsRow, error) {
			return []db.GetTopicsByJournalIdsRow{{JournalID: 7, TopicName: "work"}}, nil
		},
	}
	srv := &internalgrpc.JournalServer{}
	resp, err := srv.GetJournal(journalTestCtx(mockQuerier, noopHTTPClient()), &pb.GetJournalRequest{
		JournalId: "7",
		UserId:    userID.String(),
	})
	require.NoError(t, err)
	require.NotNil(t, resp.Journal)
	assert.Equal(t, "Full text", resp.Journal.JournalText)
	assert.Equal(t, "5", resp.Journal.UserMood)
	assert.Contains(t, resp.Journal.TopicNames, "work")
}

func TestJournalServer_GetJournal_Forbidden(t *testing.T) {
	owner := uuid.New()
	other := uuid.New()
	j := db.SourceJournal{
		ID:          1,
		UserID:      journalPgUUID(owner),
		JournalText: "x",
		MoodScore:   int32Ptr(7),
		CreatedAt:   journalPgTS(time.Now()),
		ModifiedAt:  journalPgTS(time.Now()),
	}
	mockQuerier := &mocks.QuerierMock{
		GetJournalByIdFunc: func(ctx context.Context, id int32) (db.SourceJournal, error) {
			return j, nil
		},
	}
	srv := &internalgrpc.JournalServer{}
	resp, err := srv.GetJournal(journalTestCtx(mockQuerier, noopHTTPClient()), &pb.GetJournalRequest{
		JournalId: "1",
		UserId:    other.String(),
	})
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrJournalForbidden)
}

func TestJournalServer_RequestJournalExport_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}

	resp, err := server.RequestJournalExport(context.Background(), &pb.RequestJournalExportRequest{
		UserId: "not-a-uuid",
		Format: "csv",
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestJournalServer_RequestJournalExport_UnsupportedFormat(t *testing.T) {
	server := &internalgrpc.JournalServer{}

	resp, err := server.RequestJournalExport(context.Background(), &pb.RequestJournalExportRequest{
		UserId: uuid.New().String(),
		Format: "pdf",
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "unsupported export format")
}

func TestJournalServer_RequestJournalExport_Success(t *testing.T) {
	queries := newDirectQueries(t)
	userID := createTestUser(t, queries)

	server := &internalgrpc.JournalServer{}
	ctx := inject.WithLogger(context.Background(), newTestLogger())
	ctx = inject.WithPgxPool(ctx, testPgxPool)
	ctx = inject.WithRiverClient(ctx, testRiverClient)

	resp, err := server.RequestJournalExport(ctx, &pb.RequestJournalExportRequest{
		UserId: userID.String(),
		Format: "markdown",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, "pending", resp.Status)

	exportID, err := uuid.Parse(resp.ExportId)
	require.NoError(t, err)
	t.Cleanup(func() {
		_, _ = testPgxPool.Exec(context.Background(), `DELETE FROM source.journal_exports WHERE id = $1`, exportID)
		_ = queries.DeleteUserById(context.Background(), pgtype.UUID{Bytes: userID, Valid: true})
	})

	export, err := queries.GetJournalExport(context.Background(), db.GetJournalExportParams{
		ID:     pgtype.UUID{Bytes: exportID, Valid: true},
		UserID: pgtype.UUID{Bytes: userID, Valid: true},
	})
	require.NoError(t, err)
	assert.Equal(t, db.SourceExportFormatMarkdown, export.Format)
	assert.Equal(t, db.SourceExportStatusPending, export.Status)
}

func TestJournalServer_GetJournalExport_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}

	resp, err := server.GetJournalExport(context.Background(), &pb.GetJournalExportRequest{
		UserId:   "not-a-uuid",
		ExportId: uuid.New().String(),
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestJournalServer_GetJournalExport_InvalidExportID(t *testing.T) {
	server := &internalgrpc.JournalServer{}

	resp, err := server.GetJournalExport(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), &pb.GetJournalExportRequest{
		UserId:   uuid.New().String(),
		ExportId: "not-a-uuid",
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "invalid export_id")
}

func TestJournalServer_GetJournalExport_ResponseShapes(t *testing.T) {
	userID := uuid.New()
	now := time.Date(2026, 4, 7, 10, 0, 0, 0, time.UTC)
	content := "# export"

	tests := []struct {
		name             string
		export           db.SourceJournalExport
		wantFilename     string
		wantMimeType     string
		wantContent      string
		wantEmptyContent bool
	}{
		{
			name: "complete markdown",
			export: db.SourceJournalExport{
				ID:        pgtype.UUID{Bytes: uuid.New(), Valid: true},
				UserID:    pgtype.UUID{Bytes: userID, Valid: true},
				Format:    db.SourceExportFormatMarkdown,
				Status:    db.SourceExportStatusComplete,
				Content:   &content,
				CreatedAt: pgtype.Timestamp{Time: now, Valid: true},
			},
			wantFilename: "lotus-journal-export-2026-04-07.md",
			wantMimeType: "text/markdown;charset=utf-8",
			wantContent:  "# export",
		},
		{
			name: "pending export",
			export: db.SourceJournalExport{
				ID:     pgtype.UUID{Bytes: uuid.New(), Valid: true},
				UserID: pgtype.UUID{Bytes: userID, Valid: true},
				Format: db.SourceExportFormatCsv,
				Status: db.SourceExportStatusPending,
			},
			wantEmptyContent: true,
		},
		{
			name: "complete csv",
			export: db.SourceJournalExport{
				ID:        pgtype.UUID{Bytes: uuid.New(), Valid: true},
				UserID:    pgtype.UUID{Bytes: userID, Valid: true},
				Format:    db.SourceExportFormatCsv,
				Status:    db.SourceExportStatusComplete,
				Content:   &content,
				CreatedAt: pgtype.Timestamp{Time: now, Valid: true},
			},
			wantFilename: "lotus-journal-export-2026-04-07.csv",
			wantMimeType: "text/csv;charset=utf-8",
			wantContent:  "# export",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockQuerier := &mocks.QuerierMock{
				GetJournalExportFunc: func(ctx context.Context, arg db.GetJournalExportParams) (db.SourceJournalExport, error) {
					assert.Equal(t, pgtype.UUID{Bytes: userID, Valid: true}, arg.UserID)
					return tt.export, nil
				},
			}

			resp, err := (&internalgrpc.JournalServer{}).GetJournalExport(
				journalTestCtx(mockQuerier, noopHTTPClient()),
				&pb.GetJournalExportRequest{
					UserId:   userID.String(),
					ExportId: tt.export.ID.String(),
				},
			)

			require.NoError(t, err)
			require.NotNil(t, resp)
			assert.Equal(t, tt.export.ID.String(), resp.ExportId)
			assert.Equal(t, string(tt.export.Status), resp.Status)
			if tt.wantEmptyContent {
				assert.Empty(t, resp.Content)
				assert.Empty(t, resp.Filename)
				assert.Empty(t, resp.MimeType)
			} else {
				assert.Equal(t, tt.wantContent, resp.Content)
				assert.Equal(t, tt.wantFilename, resp.Filename)
				assert.Equal(t, tt.wantMimeType, resp.MimeType)
			}
		})
	}
}
