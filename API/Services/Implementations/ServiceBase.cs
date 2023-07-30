using API.Configurations;
using API.Entities;
using API.Services.Interfaces;
using Dapper;
using Npgsql;

namespace API.Services.Implementations;

public class ServiceBase<T> : IService<T> where T : class, IEntity 
{
	private readonly string _connectionString;
	protected ServiceBase(IDbCredentials dbCredentials) { _connectionString = dbCredentials.ConnectionString; }

	public async Task<int?> CreateAsync(T entity)
	{
		using (var connection = new NpgsqlConnection(_connectionString))
		{
			return await connection.InsertAsync(entity);
		}
	}

	public async Task<T?> GetAsync(int id)
	{
		using (var connection = new NpgsqlConnection(_connectionString))
		{
			return await connection.GetAsync<T>(id);
		}
	}
	
	public async Task<int?> UpdateAsync(T entity) => throw new NotImplementedException();
	public async Task<int?> DeleteAsync(int id) => throw new NotImplementedException();

	public async Task<IEnumerable<T>?> GetAllAsync()
	{
		using(var connection = new NpgsqlConnection(_connectionString))
		{
			if (await connection.RecordCountAsync<T>() > 0)
			{
				return await connection.GetListAsync<T>();
			}

			return null;
		}
	}
	public async Task<bool> ExistsAsync(int id) => throw new NotImplementedException();
}