curl -X POST http://localhost:8080/v1/users \
     -H "Content-Type: application/json" \
     -d '{
           "email": "user@email.com",
           "password": "This123"
         }'

# /v1/oauth/users
curl -X POST http://localhost:8080/v1/oauth/users \
     -H "Content-Type: application/json" \
     -d '{
           "email": "user_oauth2@email.com",
           "oauth_provider": "github"
         }'

curl -X POST http://localhost:8080/v1/journals \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "550e8400-e29b-41d4-a716-446655440000",
           "journal_text": "This is a test journal entry.",
           "user_mood": "8"
         }'

curl -X GET "http://localhost:8080/v1/journals?user_id=fe45963c-18d9-4b03-b098-9d0eac485c21"

# known user
curl -X GET "http://localhost:8080/v1/users?email=jyablonski9@gmail.com"

# unknown user
curl -X GET "http://localhost:8080/v1/users?email=jyablonskifake@gmail.com"
