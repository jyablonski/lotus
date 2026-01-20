from feast import Entity

user_entity = Entity(
    name="user",
    description="User entity for journal summary features",
    join_keys=["user_id"],
)
