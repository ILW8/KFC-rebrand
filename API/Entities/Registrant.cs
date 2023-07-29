namespace API.Entities;

public class Registrant : EntityBase
{
	public long OsuId { get; set; }
	public string OsuName { get; set; } = null!;
	public long DiscordId { get; set; }
	public string DiscordName { get; set; } = null!;
}