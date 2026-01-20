from feast import Entity

# Define the user entity
user_entity = Entity(
    name="user",
    description="User entity for journal summary features",
    join_keys=["user_id"],
)
