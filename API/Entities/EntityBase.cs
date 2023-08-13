using Dapper;

namespace API.Entities;

public class EntityBase : IEntity
{
	[Key]
	[Column("id")]
	public int Id { get; set; }
	[Column("created_at")]
	public DateTime CreatedAt { get; set; }
	[Column("updated_at")]
	public DateTime? UpdatedAt { get; set; }
}