{
    "from": ["envs/base.docker", "/somewhere/example.com.secrets"],
    "server": {
        "host": "example.com"
    },
    "env": {
        "SERVER_ENV": "production",
        "DJANGO_DB_HOST": "db.example.com",
    }
}
