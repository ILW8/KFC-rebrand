using API.Entities;
using API.Services.Interfaces;

namespace API.Services.Implementations;

public class ServiceBase<T> : IService<T> where T : class, IEntity 
{
	// Use Dapper to implement basic implementation of CRUD operations
	
	public Task<T> CreateAsync(T entity) => throw new NotImplementedException();
	public Task<T> GetAsync(int id) => throw new NotImplementedException();
	public Task<T> UpdateAsync(T entity) => throw new NotImplementedException();
	public Task<int> DeleteAsync(int id) => throw new NotImplementedException();
	public Task<IEnumerable<T>> GetAllAsync() => throw new NotImplementedException();
	public Task<bool> ExistsAsync(int id) => throw new NotImplementedException();
}