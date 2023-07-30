using API.Entities;
using API.Services.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class CrudController<T> : Controller where T : class, IEntity
{
	private readonly ILogger _logger;
	private readonly IService<T> _service;

	public CrudController()
	{
		// Used by DI, but not by inheriting classes.
	}
	
	public CrudController(ILogger logger, IService<T> service)
	{
		// This generic logger will be provided by inheriting classes, which 
		// then get their loggers from DI.
		_logger = logger;
		_service = service;
	}

	[HttpGet("all")]
	public virtual async Task<ActionResult<IEnumerable<T>?>> GetAll()
	{
		_logger.LogInformation("Fetching all entities of type {Type}", typeof(T).Name);
		var entities = await _service.GetAllAsync();
		if(entities == null)
		{
			_logger.LogWarning("No entities of type {Type} found", typeof(T).Name);
			return NotFound("No entities exist");
		}
		
		_logger.LogInformation("Successfully fetched all entities of type {Type}", typeof(T).Name);
		return Ok(entities);
	}
	
	[HttpGet("{id}")]
	public virtual async Task<ActionResult<T?>> Get(int id)
	{
		_logger.LogInformation("Fetching entity of type {Type} with id {Id}", typeof(T).Name, id);
		var entity = await _service.GetAsync(id);
		if(entity == null)
		{
			_logger.LogWarning("No entity of type {Type} with id {Id} found", typeof(T).Name, id);
			return NotFound("No entity exists with that id");
		}
		
		_logger.LogInformation("Successfully fetched entity of type {Type} with id {Id}", typeof(T).Name, id);
		return Ok(entity);
	}
	
	[HttpPost]
	public virtual async Task<ActionResult<int?>> Create(T entity)
	{
		_logger.LogInformation("Creating entity of type {Type}", typeof(T).Name);
		int? id = await _service.CreateAsync(entity);
		if(id == null)
		{
			_logger.LogError("Failed to create entity of type {Type}", typeof(T).Name);
			return BadRequest("Failed to create entity");
		}
		
		_logger.LogInformation("Successfully created entity of type {Type}", typeof(T).Name);
		
		return Ok(id);
	}
	
	[HttpPut]
	public virtual async Task<ActionResult<int>> Update(T entity)
	{
		_logger.LogInformation("Updating entity of type {Type}", typeof(T).Name);
		int rowsAffected = await _service.UpdateAsync(entity);
		if(rowsAffected == 0)
		{
			_logger.LogError("Failed to update entity of type {Type}", typeof(T).Name);
			return BadRequest("Failed to update entity");
		}
		
		_logger.LogInformation("Successfully updated entity of type {Type}", typeof(T).Name);
		return Ok(rowsAffected);
	}
	
	[HttpDelete("{id}")]
	public virtual async Task<ActionResult<int>> Delete(int id)
	{
		_logger.LogInformation("Deleting entity of type {Type} with id {Id}", typeof(T).Name, id);
		int rowsAffected = await _service.DeleteAsync(id);
		if(rowsAffected == 0)
		{
			_logger.LogError("Failed to delete entity of type {Type} with id {Id}", typeof(T).Name, id);
			return BadRequest("Failed to delete entity");
		}
		
		_logger.LogInformation("Successfully deleted entity of type {Type} with id {Id}", typeof(T).Name, id);
		return Ok(rowsAffected);
	}
}