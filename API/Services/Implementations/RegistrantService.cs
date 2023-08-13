﻿using API.Configurations;
using API.Entities;

namespace API.Services.Implementations;

public class RegistrantService : ServiceBase<Registrant>
{
	public RegistrantService(IDbCredentials dbCredentials, ILogger<RegistrantService> logger) : base(dbCredentials, logger) {}
}