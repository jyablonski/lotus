# Tiltfile for Lotus Development Environment
# Provides hot reloading and fast iteration for all services

# ============================================================================
# Configuration Loading
# ============================================================================
config_file = "tilt_config.yaml"
watch_file(config_file)

# Load config or create default from example
if not os.path.exists(config_file):
    example_file = "tilt_config.yaml.example"
    if os.path.exists(example_file):
        local("cp {} {}".format(example_file, config_file))
        print(
            "Created {} from {}. Please review and customize if needed.".format(
                config_file, example_file
            )
        )
    else:
        fail(
            "tilt_config.yaml not found and tilt_config.yaml.example doesn't exist. Please create tilt_config.yaml"
        )

config = read_yaml(config_file)

# Validate config structure
if not config.get("services"):
    fail("tilt_config.yaml must have a 'services' section")

if not config.get("services", {}).get("enabled"):
    fail("tilt_config.yaml must have 'services.enabled' section")

# Validate that enabled services are boolean
for service, enabled in config.get("services", {}).get("enabled", {}).items():
    if enabled not in (True, False):
        fail(
            "Service '{}' in tilt_config.yaml must be true or false, got: {}".format(
                service, enabled
            )
        )

# ============================================================================
# Infrastructure Setup
# ============================================================================

# Get enabled services config
enabled_services = config.get("services", {}).get("enabled", {})
infra_config = config.get("services", {}).get("infrastructure", {})

# Build list of profiles based on enabled services
profiles = []
for service, is_enabled in enabled_services.items():
    if is_enabled:
        profiles.append(service)

# Load Docker Compose configuration with profiles
docker_compose(
    ["docker/docker-compose-local.yaml", "docker/docker-compose-tilt.yaml"],
    env_file=".env",
    profiles=profiles,
)

# Postgres is always needed if any service is enabled
if any(enabled_services.values()):
    if infra_config.get("postgres", True):
        dc_resource("postgres", labels=["infrastructure", "database"])

# MLflow starts with analyzer profile, so only configure if analyzer is enabled
if enabled_services.get("analyzer", False):
    dc_resource("mlflow", resource_deps=["postgres"], labels=["infrastructure", "ml"])

# Redis services (optional)
if infra_config.get("redis", True):
    dc_resource("redis", labels=["infrastructure", "cache"])
if infra_config.get("redisinsight", True):
    dc_resource(
        "redisinsight", resource_deps=["redis"], labels=["infrastructure", "ui"]
    )

# Suppress warnings for intermediate base images used for caching
update_settings(
    suppress_unused_image_warnings=[
        "analyzer-base",
        "django-base",
        "dagster-base",
        "dagster-webserver-base",
    ]
)

# ============================================================================
# Service Setup Functions
# ============================================================================


def setup_frontend():
    """Setup Frontend Service (Next.js)"""
    docker_build(
        "frontend",
        "services/frontend",
        dockerfile="services/frontend/Dockerfile",
        only=["package.json", "package-lock.json"],
        ignore=[
            "services/frontend/node_modules",
            "services/frontend/.next",
            "services/frontend/__tests__",
            "services/frontend/.git",
        ],
    )
    dc_resource(
        "frontend", resource_deps=["postgres", "backend"], labels=["frontend", "web"]
    )


def setup_backend():
    """Setup Backend Service (Go with Air)"""
    # Build only when dependencies change, not when source code changes
    # Air handles source code changes via volume mounts
    # Paths in 'only' are relative to the build context (services/backend)
    only_files = ["go.mod", "Dockerfile.dev", ".air.toml"]
    # Only include go.sum if it exists (it's optional in Go modules)
    if os.path.exists("services/backend/go.sum"):
        only_files.append("go.sum")

    docker_build(
        "backend",
        "services/backend",
        dockerfile="services/backend/Dockerfile.dev",
        only=only_files,
        ignore=[
            "services/backend/lotus",
            "services/backend/.git",
            "services/backend/vendor",
            "services/backend/tmp",
        ],
    )
    dc_resource("backend", resource_deps=["postgres"], labels=["backend", "api"])


def setup_analyzer():
    """Setup Analyzer Service (Python FastAPI)"""
    docker_build(
        "analyzer-base",
        "services/analyzer",
        dockerfile="services/analyzer/Dockerfile",
        only=["services/analyzer/pyproject.toml", "services/analyzer/uv.lock"],
        target="python-deps",
        build_args={"INSTALL_DEV_DEPENDENCIES": "true"},
    )
    docker_build(
        "analyzer",
        "services/analyzer",
        dockerfile="services/analyzer/Dockerfile",
        target="runtime",
        build_args={"INSTALL_DEV_DEPENDENCIES": "true"},
        ignore=[
            "services/analyzer/.venv",
            "services/analyzer/__pycache__",
            "services/analyzer/tests",
            "services/analyzer/*.pyc",
            "services/analyzer/.git",
        ],
    )
    dc_resource(
        "analyzer",
        resource_deps=["postgres", "mlflow"],
        labels=["analyzer", "ml", "api"],
    )


def setup_django_admin():
    """Setup Django Admin Service"""
    docker_build(
        "django-base",
        "services/django",
        dockerfile="services/django/Dockerfile",
        only=["services/django/pyproject.toml", "services/django/uv.lock"],
        target="python-deps",
        build_args={"INSTALL_DEV_DEPENDENCIES": "true"},
    )
    docker_build(
        "django_admin",
        "services/django",
        dockerfile="services/django/Dockerfile",
        target="runtime",
        build_args={"INSTALL_DEV_DEPENDENCIES": "true"},
        ignore=[
            "services/django/.venv",
            "services/django/__pycache__",
            "services/django/tests",
            "services/django/*.pyc",
            "services/django/.git",
        ],
    )
    dc_resource(
        "django_admin",
        resource_deps=["postgres", "analyzer"],
        labels=["django", "admin", "web"],
    )


def setup_dagster_grpc_server():
    """Setup Dagster gRPC Server"""
    docker_build(
        "dagster-base",
        ".",
        dockerfile="services/dagster/Dockerfile",
        only=["services/dagster/pyproject.toml", "services/dagster/uv.lock"],
        target="builder",
    )
    # Build runtime image - don't use only/ignore to avoid cache key issues
    # The Dockerfile handles what gets copied
    docker_build(
        "dagster_server_image",
        ".",
        dockerfile="services/dagster/Dockerfile",
        target="runtime",
        ignore=[
            "services/dagster/.venv",
            "services/dagster/__pycache__",
            "services/dagster/tests",
            "services/dagster/*.pyc",
            "services/dagster/.git",
            "services/dbt/.venv",
            "services/dbt/__pycache__",
            "services/dbt/target",
            "services/dbt/.git",
        ],
    )
    dc_resource(
        "dagster_grpc_server", resource_deps=["postgres"], labels=["dagster", "data"]
    )


def setup_dagster_webserver():
    """Setup Dagster Webserver"""
    docker_build(
        "dagster-webserver-base",
        "services/dagster",
        dockerfile="services/dagster/Dockerfile.webserver",
        only=["services/dagster/pyproject.toml", "services/dagster/uv.lock"],
        target="builder",
    )
    docker_build(
        "dagster_webserver",
        "services/dagster",
        dockerfile="services/dagster/Dockerfile.webserver",
        target="runtime",
    )
    dc_resource(
        "dagster_webserver",
        resource_deps=["postgres", "dagster_grpc_server"],
        labels=["dagster", "ui"],
    )


def setup_dagster_daemon():
    """Setup Dagster Daemon"""
    docker_build(
        "dagster_daemon",
        "services/dagster",
        dockerfile="services/dagster/Dockerfile.webserver",
        target="runtime",
    )
    dc_resource(
        "dagster_daemon",
        resource_deps=["postgres", "dagster_grpc_server"],
        labels=["dagster"],
    )


def setup_dagster():
    """Setup all Dagster services (grpc_server, webserver, daemon)"""
    setup_dagster_grpc_server()
    setup_dagster_webserver()
    setup_dagster_daemon()


# ============================================================================
# Service Registry
# ============================================================================
service_functions = {
    "frontend": setup_frontend,
    "backend": setup_backend,
    "analyzer": setup_analyzer,
    "django_admin": setup_django_admin,
    "dagster": setup_dagster,
}

# ============================================================================
# Setup Enabled Services
# ============================================================================
enabled = config.get("services", {}).get("enabled", {})

for service_name, is_enabled in enabled.items():
    if is_enabled:
        if service_name in service_functions:
            service_functions[service_name]()
        else:
            print(
                "Warning: Unknown service '{}' in tilt_config.yaml".format(service_name)
            )

# ============================================================================
# Configuration Notes
# ============================================================================
# Note: Port forwarding is handled by docker-compose ports configuration
# No need for port_forwards with dc_resource - ports are already exposed
