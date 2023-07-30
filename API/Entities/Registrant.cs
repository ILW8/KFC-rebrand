using Dapper;

namespace API.Entities;

[Table("registrants")]
public class Registrant : EntityBase
{
	[Column("osu_id")]
	public long OsuId { get; set; }
	[Column("osu_name")]
	public string OsuName { get; set; } = null!;
	[Column("discord_id")]
	public long DiscordId { get; set; }
	[Column("discord_name")]
	public string DiscordName { get; set; } = null!;
}