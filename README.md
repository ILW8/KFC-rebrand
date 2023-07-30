# 2024 API

## Setup
- [Install .NET 7](https://dotnet.microsoft.com/en-us/download/dotnet/7.0)
- [Install Docker](https://www.docker.com/) (Docker desktop is fine)
- Clone the repo and `cd` into it
- Run `sh database-setup/db-test.sh` (or copy and paste the docker command yourself). This starts a PostgreSQL database on your system (make sure nothing is already occupying port 5432)
- Using a database browser, connect to the database (view credentials below), and run the `database-setup/schema.sql` script.
- Create this file under `./API`, don't change the contents:
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Port=5432;User Id=postgres;Password=postgres;"
  }
}
```
- You can now load the .sln file into your favorite IDE and begin debugging. Make sure you have the docker database running each time you debug.