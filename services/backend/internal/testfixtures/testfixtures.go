package testfixtures

import (
	"context"
	"reflect"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
)

type Model interface {
	db.SourceUser |
		db.SourceJournal |
		db.SourceUserGameBalance |
		db.SourceUserGameBet |
		db.SourceJournalExport |
		db.SourceJournalCommunityProjection |
		db.SourceCommunityThemeRollup |
		db.SourceCommunityMoodRollup |
		db.SourceCommunitySummary |
		db.SourceCommunityPromptSet |
		db.SourceRuntimeConfig
}

// BuildDefaultModel returns a valid baseline model without persisting it.
func BuildDefaultModel[T Model](t *testing.T, model T) T {
	t.Helper()

	suffix := uuid.New().String()
	today := Date(time.Now().Year(), time.Now().Month(), time.Now().Day())

	switch any(model).(type) {
	case db.SourceUser:
		provider := "test"
		return any(db.SourceUser{
			Email:         "test-" + suffix + "@test.example",
			OauthProvider: &provider,
		}).(T)
	case db.SourceJournal:
		return any(db.SourceJournal{
			JournalText: "test journal " + suffix,
			MoodScore:   Int32Ptr(3),
		}).(T)
	case db.SourceUserGameBalance:
		return any(db.SourceUserGameBalance{
			Balance: 100,
		}).(T)
	case db.SourceUserGameBet:
		return any(db.SourceUserGameBet{
			Zone:       "safe",
			Amount:     10,
			RollResult: 50,
			Payout:     20,
		}).(T)
	case db.SourceJournalExport:
		return any(db.SourceJournalExport{
			Format: db.SourceExportFormatMarkdown,
			Status: db.SourceExportStatusPending,
		}).(T)
	case db.SourceJournalCommunityProjection:
		return any(db.SourceJournalCommunityProjection{
			EligibleForCommunity: true,
			EntryLocalDate:       today,
			PrimaryMood:          StringPtr("calm"),
			PrimarySentiment:     StringPtr("positive"),
			ThemeNames:           []string{"gratitude"},
			AnalysisVersion:      "test-v1",
		}).(T)
	case db.SourceCommunityThemeRollup:
		return any(db.SourceCommunityThemeRollup{
			BucketDate:      today,
			TimeGrain:       "day",
			ScopeType:       "global",
			ScopeValue:      "test-" + suffix,
			ThemeName:       "gratitude",
			EntryCount:      1,
			UniqueUserCount: 1,
			Rank:            1,
		}).(T)
	case db.SourceCommunityMoodRollup:
		return any(db.SourceCommunityMoodRollup{
			BucketDate:      today,
			TimeGrain:       "day",
			ScopeType:       "global",
			ScopeValue:      "test-" + suffix,
			MoodName:        "calm",
			EntryCount:      1,
			UniqueUserCount: 1,
			Rank:            1,
		}).(T)
	case db.SourceCommunitySummary:
		return any(db.SourceCommunitySummary{
			BucketDate:       today,
			TimeGrain:        "day",
			ScopeType:        "global",
			ScopeValue:       "test-" + suffix,
			SummaryText:      "test community summary",
			SourceThemeNames: []string{"gratitude"},
			SourceMoodNames:  []string{"calm"},
			GenerationMethod: "test",
		}).(T)
	case db.SourceCommunityPromptSet:
		return any(db.SourceCommunityPromptSet{
			BucketDate:       today,
			TimeGrain:        "day",
			ScopeType:        "global",
			ScopeValue:       "test-" + suffix,
			PromptSetJson:    []byte(`["What helped today?"]`),
			SourceThemeNames: []string{"gratitude"},
			SourceMoodNames:  []string{"calm"},
			GenerationMethod: "test",
		}).(T)
	case db.SourceRuntimeConfig:
		return any(db.SourceRuntimeConfig{
			Key:         "test." + suffix,
			Value:       []byte(`{"enabled":true}`),
			Service:     "backend",
			Description: "test runtime config",
		}).(T)
	default:
		t.Fatalf("testfixtures: %T is not registered; add an insert query or fixture case", model)
	}

	var zero T
	return zero
}

// Create persists a fully populated model using sqlc query methods.
func Create[T Model](t *testing.T, ctx context.Context, q *db.Queries, model T) T {
	t.Helper()

	switch v := any(model).(type) {
	case db.SourceUser:
		return any(createUser(t, ctx, q, v)).(T)
	case db.SourceJournal:
		created, err := q.CreateJournal(ctx, db.CreateJournalParams{
			UserID:      v.UserID,
			JournalText: v.JournalText,
			MoodScore:   v.MoodScore,
		})
		requireNoError(t, "CreateJournal", err)
		return any(created).(T)
	case db.SourceUserGameBalance:
		created, err := q.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
			UserID:  v.UserID,
			Balance: v.Balance,
		})
		requireNoError(t, "UpsertUserGameBalance", err)
		return any(created).(T)
	case db.SourceUserGameBet:
		created, err := q.InsertUserGameBet(ctx, db.InsertUserGameBetParams{
			UserID:     v.UserID,
			Zone:       v.Zone,
			Amount:     v.Amount,
			RollResult: v.RollResult,
			Payout:     v.Payout,
		})
		requireNoError(t, "InsertUserGameBet", err)
		return any(created).(T)
	case db.SourceJournalExport:
		created, err := q.CreateJournalExport(ctx, db.CreateJournalExportParams{
			UserID: v.UserID,
			Format: v.Format,
		})
		requireNoError(t, "CreateJournalExport", err)
		return any(created).(T)
	case db.SourceJournalCommunityProjection:
		created, err := q.UpsertJournalCommunityProjection(ctx, db.UpsertJournalCommunityProjectionParams{
			JournalID:            v.JournalID,
			UserID:               v.UserID,
			EligibleForCommunity: v.EligibleForCommunity,
			EntryLocalDate:       v.EntryLocalDate,
			PrimaryMood:          v.PrimaryMood,
			PrimarySentiment:     v.PrimarySentiment,
			ThemeNames:           v.ThemeNames,
			CountryCode:          v.CountryCode,
			RegionCode:           v.RegionCode,
			AnalysisVersion:      v.AnalysisVersion,
		})
		requireNoError(t, "UpsertJournalCommunityProjection", err)
		return any(created).(T)
	case db.SourceCommunityThemeRollup:
		created, err := q.UpsertCommunityThemeRollup(ctx, db.UpsertCommunityThemeRollupParams{
			BucketDate:      v.BucketDate,
			TimeGrain:       v.TimeGrain,
			ScopeType:       v.ScopeType,
			ScopeValue:      v.ScopeValue,
			ThemeName:       v.ThemeName,
			EntryCount:      v.EntryCount,
			UniqueUserCount: v.UniqueUserCount,
			Rank:            v.Rank,
			DeltaVsPrevious: v.DeltaVsPrevious,
		})
		requireNoError(t, "UpsertCommunityThemeRollup", err)
		return any(created).(T)
	case db.SourceCommunityMoodRollup:
		created, err := q.UpsertCommunityMoodRollup(ctx, db.UpsertCommunityMoodRollupParams{
			BucketDate:      v.BucketDate,
			TimeGrain:       v.TimeGrain,
			ScopeType:       v.ScopeType,
			ScopeValue:      v.ScopeValue,
			MoodName:        v.MoodName,
			EntryCount:      v.EntryCount,
			UniqueUserCount: v.UniqueUserCount,
			Rank:            v.Rank,
			DeltaVsPrevious: v.DeltaVsPrevious,
		})
		requireNoError(t, "UpsertCommunityMoodRollup", err)
		return any(created).(T)
	case db.SourceCommunitySummary:
		created, err := q.UpsertCommunitySummary(ctx, db.UpsertCommunitySummaryParams{
			BucketDate:       v.BucketDate,
			TimeGrain:        v.TimeGrain,
			ScopeType:        v.ScopeType,
			ScopeValue:       v.ScopeValue,
			SummaryText:      v.SummaryText,
			SourceThemeNames: v.SourceThemeNames,
			SourceMoodNames:  v.SourceMoodNames,
			GenerationMethod: v.GenerationMethod,
		})
		requireNoError(t, "UpsertCommunitySummary", err)
		return any(created).(T)
	case db.SourceCommunityPromptSet:
		created, err := q.UpsertCommunityPromptSet(ctx, db.UpsertCommunityPromptSetParams{
			BucketDate:       v.BucketDate,
			TimeGrain:        v.TimeGrain,
			ScopeType:        v.ScopeType,
			ScopeValue:       v.ScopeValue,
			PromptSetJson:    v.PromptSetJson,
			SourceThemeNames: v.SourceThemeNames,
			SourceMoodNames:  v.SourceMoodNames,
			GenerationMethod: v.GenerationMethod,
		})
		requireNoError(t, "UpsertCommunityPromptSet", err)
		return any(created).(T)
	case db.SourceRuntimeConfig:
		created, err := q.UpsertRuntimeConfigValue(ctx, db.UpsertRuntimeConfigValueParams{
			Key:         v.Key,
			Value:       v.Value,
			Service:     v.Service,
			Description: v.Description,
		})
		requireNoError(t, "UpsertRuntimeConfigValue", err)
		return any(created).(T)
	default:
		t.Fatalf("testfixtures: %T is not registered; add an insert query or fixture case", model)
	}

	var zero T
	return zero
}

// CreateWithDefaults merges caller-provided fields over defaults, resolves
// required parent records, and persists the resulting model.
func CreateWithDefaults[T Model](t *testing.T, ctx context.Context, q *db.Queries, model T, fieldsToEmpty ...string) T {
	t.Helper()

	merged := BuildDefaultModel(t, model)
	mergeNonZeroFields(t, &merged, model, fieldsToEmpty)
	resolveDependencies(t, ctx, q, &merged)

	return Create(t, ctx, q, merged)
}

func createUser(t *testing.T, ctx context.Context, q *db.Queries, user db.SourceUser) db.SourceUser {
	t.Helper()

	var created db.SourceUser
	if user.OauthProvider != nil {
		var err error
		created, err = q.CreateUserOauth(ctx, db.CreateUserOauthParams{
			Email:         user.Email,
			OauthProvider: user.OauthProvider,
		})
		requireNoError(t, "CreateUserOauth", err)
	} else {
		var err error
		created, err = q.CreateUser(ctx, db.CreateUserParams{
			Email:    user.Email,
			Password: user.Password,
			Salt:     user.Salt,
		})
		requireNoError(t, "CreateUser", err)
	}

	if user.Timezone != "" {
		var err error
		created, err = q.UpdateUserTimezone(ctx, db.UpdateUserTimezoneParams{
			ID:       created.ID,
			Timezone: user.Timezone,
		})
		requireNoError(t, "UpdateUserTimezone", err)
	}

	if user.CommunityInsightsOptIn || user.CommunityLocationOptIn || user.CommunityCountryCode != nil || user.CommunityRegionCode != nil {
		var err error
		created, err = q.UpdateCommunitySettingsByUserId(ctx, db.UpdateCommunitySettingsByUserIdParams{
			ID:                     created.ID,
			CommunityInsightsOptIn: user.CommunityInsightsOptIn,
			CommunityLocationOptIn: user.CommunityLocationOptIn,
			CommunityCountryCode:   user.CommunityCountryCode,
			CommunityRegionCode:    user.CommunityRegionCode,
		})
		requireNoError(t, "UpdateCommunitySettingsByUserId", err)
	}

	return created
}

func resolveDependencies[T Model](t *testing.T, ctx context.Context, q *db.Queries, model *T) {
	t.Helper()

	switch v := any(model).(type) {
	case *db.SourceJournal:
		if isZeroUUID(v.UserID) {
			user := CreateWithDefaults(t, ctx, q, db.SourceUser{})
			v.UserID = user.ID
		}
	case *db.SourceUserGameBalance:
		if isZeroUUID(v.UserID) {
			user := CreateWithDefaults(t, ctx, q, db.SourceUser{})
			v.UserID = user.ID
		}
	case *db.SourceUserGameBet:
		if isZeroUUID(v.UserID) {
			user := CreateWithDefaults(t, ctx, q, db.SourceUser{})
			v.UserID = user.ID
		}
	case *db.SourceJournalExport:
		if isZeroUUID(v.UserID) {
			user := CreateWithDefaults(t, ctx, q, db.SourceUser{})
			v.UserID = user.ID
		}
	case *db.SourceJournalCommunityProjection:
		if v.JournalID == 0 {
			journal := CreateWithDefaults(t, ctx, q, db.SourceJournal{UserID: v.UserID})
			v.JournalID = journal.ID
			v.UserID = journal.UserID
			return
		}
		if isZeroUUID(v.UserID) {
			t.Fatalf("testfixtures: SourceJournalCommunityProjection requires UserID when JournalID is supplied")
		}
	}
}

func mergeNonZeroFields[T Model](t *testing.T, target *T, input T, fieldsToEmpty []string) {
	t.Helper()

	targetValue := reflect.ValueOf(target)
	if targetValue.Kind() != reflect.Pointer || targetValue.Elem().Kind() != reflect.Struct {
		t.Fatalf("testfixtures: merge target must be a pointer to a struct, got %T", target)
	}

	inputValue := reflect.ValueOf(input)
	if inputValue.Kind() != reflect.Struct {
		t.Fatalf("testfixtures: merge input must be a struct, got %T", input)
	}

	targetStruct := targetValue.Elem()
	emptyFields := fieldsToEmptySet(t, inputValue.Type(), fieldsToEmpty)
	for i := 0; i < inputValue.NumField(); i++ {
		fieldInfo := inputValue.Type().Field(i)
		if fieldInfo.PkgPath != "" {
			continue
		}

		targetField := targetStruct.Field(i)
		if !targetField.CanSet() {
			continue
		}

		if emptyFields[fieldInfo.Name] {
			targetField.Set(reflect.Zero(targetField.Type()))
			continue
		}

		inputField := inputValue.Field(i)
		if !inputField.IsZero() {
			targetField.Set(inputField)
		}
	}
}

func fieldsToEmptySet(t *testing.T, typ reflect.Type, fieldNames []string) map[string]bool {
	t.Helper()

	fields := make(map[string]bool, len(fieldNames))
	for _, name := range fieldNames {
		field, ok := typ.FieldByName(name)
		if !ok || field.PkgPath != "" {
			t.Fatalf("testfixtures: %s has no exported field %q", typ.Name(), name)
		}
		fields[name] = true
	}
	return fields
}

func isZeroUUID(id pgtype.UUID) bool {
	if !id.Valid {
		return true
	}
	return id.Bytes == [16]byte{}
}

func requireNoError(t *testing.T, op string, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("testfixtures: %s: %v", op, err)
	}
}
