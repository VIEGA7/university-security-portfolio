using System.Collections.Concurrent;
using System.Security.Claims;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.AspNetCore.DataProtection;

// Reconstructed from reports 5, 15, 16. This is a new, combined cookie demo.
// Historical JWT snippets were NOT promoted to a production identity provider.
var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Services.AddDataProtection().PersistKeysToFileSystem(
    new DirectoryInfo(Path.Combine(builder.Environment.ContentRootPath, "data", "keys")));
var accounts = new Dictionary<string, Account>(StringComparer.OrdinalIgnoreCase);
var hasher = new PasswordHasher<Account>();
foreach (var (prefix, role) in new[] { ("DEMO_ADMIN", "admin"), ("DEMO_READER", "reader") })
{
    var name = Environment.GetEnvironmentVariable(prefix + "_USER");
    var password = Environment.GetEnvironmentVariable(prefix + "_PASSWORD");
    if (string.IsNullOrWhiteSpace(name) || name.Length > 100 || password is null || password.Length < 12)
        throw new InvalidOperationException($"Set {prefix}_USER and {prefix}_PASSWORD (at least 12 characters).");
    var account = new Account(name, role);
    account.PasswordHash = hasher.HashPassword(account, password);
    if (!accounts.TryAdd(name, account))
        throw new InvalidOperationException("Admin and reader must have distinct usernames.");
}
// Equal-cost password verification for unknown users.
var dummy = new Account("dummy", "none");
dummy.PasswordHash = hasher.HashPassword(dummy, Guid.NewGuid().ToString());

builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.Cookie.Name = "portfolio.session";
        options.Cookie.HttpOnly = true;
        options.Cookie.SameSite = SameSiteMode.Strict;
        options.Cookie.SecurePolicy = builder.Environment.IsDevelopment()
            ? CookieSecurePolicy.SameAsRequest : CookieSecurePolicy.Always;
        options.ExpireTimeSpan = TimeSpan.FromMinutes(15);
        options.SlidingExpiration = false;
        options.Events.OnRedirectToLogin = context =>
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            return Task.CompletedTask;
        };
        options.Events.OnRedirectToAccessDenied = context =>
        {
            context.Response.StatusCode = StatusCodes.Status403Forbidden;
            return Task.CompletedTask;
        };
    });
builder.Services.AddAuthorization();
builder.Services.AddAntiforgery(options =>
{
    options.HeaderName = "X-CSRF-TOKEN";
    options.Cookie.Name = "portfolio.csrf";
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.Cookie.SecurePolicy = builder.Environment.IsDevelopment()
        ? CookieSecurePolicy.SameAsRequest : CookieSecurePolicy.Always;
});
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    // Global limiter is intentional for this single-process, local demo.
    options.AddFixedWindowLimiter("login", limiter =>
    {
        limiter.PermitLimit = 5;
        limiter.Window = TimeSpan.FromMinutes(1);
        limiter.QueueLimit = 0;
    });
});
var app = builder.Build();
app.Use(async (context, next) =>
{
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["Content-Security-Policy"] =
        "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'";
    context.Response.Headers.CacheControl = "no-store";
    await next(context);
});
app.UseDefaultFiles();
app.UseStaticFiles();
app.UseAuthentication();
app.UseAuthorization();
app.UseRateLimiter();

app.MapGet("/api/csrf", (HttpContext context, IAntiforgery antiforgery) =>
    Results.Ok(new { token = antiforgery.GetAndStoreTokens(context).RequestToken }));

async ValueTask<object?> ValidateCsrf(EndpointFilterInvocationContext invocation, EndpointFilterDelegate next)
{
    var context = invocation.HttpContext;
    try
    {
        await context.RequestServices.GetRequiredService<IAntiforgery>().ValidateRequestAsync(context);
    }
    catch (AntiforgeryValidationException)
    {
        return Results.BadRequest(new { error = "Missing or invalid CSRF token." });
    }
    return await next(invocation);
}

app.MapPost("/api/login", async (LoginRequest request, HttpContext context) =>
{
    if (string.IsNullOrWhiteSpace(request.Username) || request.Username.Length > 100 ||
        request.Password is null || request.Password.Length > 1024)
        return Results.BadRequest();
    var known = accounts.TryGetValue(request.Username, out var account);
    account ??= dummy;
    var valid = hasher.VerifyHashedPassword(account, account.PasswordHash, request.Password);
    if (!known || valid == PasswordVerificationResult.Failed)
        return Results.Unauthorized();
    var identity = new ClaimsIdentity(new[] {
        new Claim(ClaimTypes.Name, account.Username), new Claim(ClaimTypes.Role, account.Role)
    }, CookieAuthenticationDefaults.AuthenticationScheme);
    await context.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, new ClaimsPrincipal(identity),
        new AuthenticationProperties { IsPersistent = false });
    return Results.Ok(new { username = account.Username, role = account.Role });
}).RequireRateLimiting("login").AddEndpointFilter(ValidateCsrf);

app.MapPost("/api/logout", async (HttpContext context) =>
{
    await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    return Results.NoContent();
}).RequireAuthorization().AddEndpointFilter(ValidateCsrf);

app.MapGet("/api/me", (HttpContext context) => Results.Ok(new {
    username = context.User.Identity!.Name,
    role = context.User.FindFirstValue(ClaimTypes.Role)
})).RequireAuthorization();

var people = new ConcurrentDictionary<int, Person>();
people[1] = new Person(1, "Demo User", 22);
int nextId = 1;
app.MapGet("/api/users", () => Results.Ok(people.Values.OrderBy(p => p.Id))).RequireAuthorization();
app.MapGet("/api/users/{id:int}", (int id) => people.TryGetValue(id, out var person)
    ? Results.Ok(person) : Results.NotFound()).RequireAuthorization();

static bool Valid(PersonInput person) => !string.IsNullOrWhiteSpace(person.Name) &&
    person.Name.Trim().Length <= 100 && person.Age is >= 0 and <= 130;
var admin = app.MapGroup("/api/users").RequireAuthorization(policy => policy.RequireRole("admin"));
admin.AddEndpointFilter(ValidateCsrf);
admin.MapPost("", (PersonInput request) =>
{
    if (!Valid(request)) return Results.BadRequest(new { error = "Name: 1..100 characters; age: 0..130." });
    var person = new Person(Interlocked.Increment(ref nextId), request.Name!.Trim(), request.Age);
    people[person.Id] = person;
    return Results.Created($"/api/users/{person.Id}", person);
});
admin.MapPut("/{id:int}", (int id, PersonInput request) =>
{
    if (!Valid(request)) return Results.BadRequest();
    if (!people.TryGetValue(id, out var old)) return Results.NotFound();
    var updated = new Person(id, request.Name!.Trim(), request.Age);
    return people.TryUpdate(id, updated, old) ? Results.Ok(updated) : Results.Conflict();
});
admin.MapDelete("/{id:int}", (int id) => people.TryRemove(id, out _)
    ? Results.NoContent() : Results.NotFound());

app.Run();
record LoginRequest(string? Username, string? Password);
record PersonInput(string? Name, int Age);
record Person(int Id, string Name, int Age);
sealed class Account(string username, string role)
{
    public string Username { get; } = username;
    public string Role { get; } = role;
    public string PasswordHash { get; set; } = "";
}
