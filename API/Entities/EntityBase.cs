using Dapper;

namespace API.Entities;

public class EntityBase : IEntity
{
	[Key]
	public int Id { get; set; }
	public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
	public DateTime? UpdatedAt { get; set; }
}