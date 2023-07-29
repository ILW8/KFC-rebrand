namespace API.Entities;

public class EntityBase : IEntity
{
	public int Id { get; set; }
	public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
	public DateTime? UpdatedAt { get; set; }
}