using API.Entities;
using API.Services.Interfaces;

namespace API.Controllers;

public class RegistrantsController : CrudController<Registrant>
{
	public RegistrantsController(ILogger<RegistrantsController> logger, IRegistrantService service) : base(logger, service)
	{
		
	}
}