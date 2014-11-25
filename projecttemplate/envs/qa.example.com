{
    "from": ["envs/base.docker", "/somewhere/qa.example.com.secrets"],
    "server": {
        "host": "qa.example.com"
    },
    "env": {
        "DJANGO_ENVIRONMENT": "qa",
        "DJANGO_DB_HOST": "qadb.example.com",
    }
}
