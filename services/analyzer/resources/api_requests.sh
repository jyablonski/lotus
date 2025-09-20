curl https: //api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-zzz"

curl https: //api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-proj-zzz" \
  -d '{
    "model": "gpt-5-nano-2025-08-07",
    "messages": [
        {
            "role": "user",
            "content": "Hello"
        }
    ],
    "max_completion_tokens": 10
}'



curl POST http: //localhost:8083/v1/journals/1/sentiment/analyze \
-H "Content-Type: application/json" \
-d '{}' \
-v

curl -X PUT http: //localhost:8083/v1/journals/1/sentiment \
-H "Content-Type: application/json" \
-d '{}' \
-v

curl -X POST http: //localhost:8083/v1/journals/20/openai/topics \
-H "Content-Type: application/json" \
-v

curl -X POST http://localhost:8083/journals/1/topics \
  -H "Content-Type: application/json" \
  -v

curl -X POST http://localhost:8083/v1/journals/topics \
     -H "Content-Type: application/json" \
     -d '{
           "journal_id": "1"
         }'

curl -X POST http://localhost:8083/v1/journals/1/topics \
-H "Content-Type: application/json" \
-v

curl -X POST http://localhost:8083/v1/journals/2/topics \
-H "Content-Type: application/json" \
-v

curl -X POST http://localhost:8083/v1/journals/3/topics \
-H "Content-Type: application/json" \
-v

curl -X POST http://localhost:8083/v1/journals/4/topics \
-H "Content-Type: application/json" \
-v

curl -X GET http://localhost:8083/v1/journals/19/topics \
-H "Content-Type: application/json" \
-v