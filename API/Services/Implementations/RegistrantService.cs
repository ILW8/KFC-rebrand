using API.Configurations;
using API.Entities;
using API.Services.Interfaces;

namespace API.Services.Implementations;

public class RegistrantService : ServiceBase<Registrant>, IRegistrantService
{
	public RegistrantService(IDbCredentials dbCredentials) : base(dbCredentials) {}
}