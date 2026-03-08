package contract_test

import (
	"fmt"
	"io"
	"net/http"
	"strings"
	"testing"

	"github.com/pact-foundation/pact-go/v2/consumer"
	"github.com/pact-foundation/pact-go/v2/matchers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestBackendAnalyzerContract_TriggerSentiment(t *testing.T) {
	mockProvider, err := consumer.NewV3Pact(consumer.MockHTTPProviderConfig{
		Consumer: "LotusBackend",
		Provider: "LotusAnalyzer",
		PactDir:  "../../../pacts",
	})
	require.NoError(t, err)

	err = mockProvider.
		AddInteraction().
		Given("a journal entry exists in the analyzer database").
		UponReceiving("a request to trigger sentiment analysis").
		WithRequest("PUT", "/v1/journals/123/sentiment", func(b *consumer.V3RequestBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(map[string]interface{}{
				"force_reanalyze": matchers.Like(false),
			})
		}).
		WillRespondWith(200, func(b *consumer.V3ResponseBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(map[string]interface{}{
				"id":               matchers.Like(1),
				"journal_id":       matchers.Like(123),
				"sentiment":        matchers.Like("positive"),
				"confidence":       matchers.Like(0.85),
				"confidence_level": matchers.Like("high"),
				"is_reliable":      matchers.Like(true),
				"ml_model_version": matchers.Like("v1.0.0"),
				"created_at":       matchers.Like("2026-01-15T10:00:00Z"),
			})
		}).
		ExecuteTest(t, func(config consumer.MockServerConfig) error {
			url := fmt.Sprintf("http://%s:%d/v1/journals/123/sentiment", config.Host, config.Port)

			body := strings.NewReader(`{"force_reanalyze":false}`)
			req, err := http.NewRequest("PUT", url, body)
			if err != nil {
				return err
			}
			req.Header.Set("Content-Type", "application/json")

			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)

			respBody, err := io.ReadAll(resp.Body)
			if err != nil {
				return err
			}
			assert.Contains(t, string(respBody), "sentiment")

			return nil
		})

	require.NoError(t, err)
}

func TestBackendAnalyzerContract_TriggerTopics(t *testing.T) {
	mockProvider, err := consumer.NewV3Pact(consumer.MockHTTPProviderConfig{
		Consumer: "LotusBackend",
		Provider: "LotusAnalyzer",
		PactDir:  "../../../pacts",
	})
	require.NoError(t, err)

	err = mockProvider.
		AddInteraction().
		Given("a journal entry exists in the analyzer database").
		UponReceiving("a request to trigger OpenAI topic extraction").
		WithRequest("POST", "/v1/journals/123/openai/topics", func(b *consumer.V3RequestBuilder) {
			b.Header("Content-Type", matchers.S("application/json"))
			b.JSONBody(map[string]interface{}{
				"force_reanalyze": matchers.Like(false),
			})
		}).
		WillRespondWith(204).
		ExecuteTest(t, func(config consumer.MockServerConfig) error {
			url := fmt.Sprintf("http://%s:%d/v1/journals/123/openai/topics", config.Host, config.Port)

			body := strings.NewReader(`{"force_reanalyze":false}`)
			req, err := http.NewRequest("POST", url, body)
			if err != nil {
				return err
			}
			req.Header.Set("Content-Type", "application/json")

			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 204, resp.StatusCode)
			return nil
		})

	require.NoError(t, err)
}
