from argon2 import PasswordHasher

# Default values are:
# RFC_9106_LOW_MEMORY = Parameters(
#     type=Type.ID,
#     version=19,
#     salt_len=16,
#     hash_len=32,
#     time_cost=3,
#     memory_cost=65536,  # 64 MiB
#     parallelism=4
# )
password_hasher = PasswordHasher()
