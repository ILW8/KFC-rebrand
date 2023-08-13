﻿using API.Entities;

namespace API.Services.Interfaces;

public interface IService<T> where T : class, IEntity
{
	// CRUD operations
	
	/// <summary>
	///  Adds a new entity to the database. If successful, returns the primary key of the entity, otherwise null.
	/// </summary>
	Task<int?> CreateAsync(T entity);

	/// <summary>
	///  Gets an entity from the database by its ID. Returns null if not found.
	/// </summary>
	Task<T?> GetAsync(int id);

	/// <summary>
	///  Updates an entity in the database by its ID. Returns the number of rows affected.
	/// </summary>
	Task<int?> UpdateAsync(T entity);

	/// <summary>
	///  Deletes an entity from the database by its ID. Returns the number of rows affected.
	/// </summary>
	Task<int?> DeleteAsync(int id);

	// Other common operations
	
	/// <summary>
	/// Gets all entities from the database. If successful, returns the collection of entities, otherwise null.
	/// </summary>
	Task<IEnumerable<T>?> GetAllAsync();
	/// <summary>
	/// Returns true if an entity with the given ID exists in the database.
	/// </summary>
	Task<bool> ExistsAsync(int id);
}