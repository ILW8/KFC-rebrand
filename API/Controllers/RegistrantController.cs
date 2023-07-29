using API.Entities;
using API.Services.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace API.Controllers;

public class RegistrantController : CrudController<Registrant>
{
	public RegistrantController(ILogger<RegistrantController> logger, IService<Registrant> service) : base(logger, service)
	{
		
	}
}