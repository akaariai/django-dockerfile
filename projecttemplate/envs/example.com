{
    "from": ["envs/base.docker", "/somewhere/example.com.secrets"],
    "server": {
        "host": "example.com"
    },
    "env": {
        "DJANGO_ENVIRONMENT": "production",
        "DJANGO_DB_HOST": "db.example.com",
    }
}
