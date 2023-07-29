using API.Entities;

namespace API.Services.Interfaces;

public interface IService<T> where T : class, IEntity
{
	// CRUD operations
	Task<T> CreateAsync(T entity);
	Task<T> GetAsync(int id);
	Task<T> UpdateAsync(T entity);
	Task<int> DeleteAsync(int id);
	
	// Other common operations
	Task<IEnumerable<T>> GetAllAsync();
	Task<bool> ExistsAsync(int id);
}