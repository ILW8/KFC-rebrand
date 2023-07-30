create table if not exists registrants
(
    id           serial
        constraint registrants_pk
            primary key,
    osu_id       bigint    not null
        constraint registrants_osu_id
            unique,
    discord_id   bigint    not null
        constraint registrants_discord_id
            unique,
    osu_name     text      not null,
    discord_name text      not null,
    created_at   timestamp not null,
    updated_at   timestamp
);
