// based on https://developers.cloudflare.com/workers/examples/cors-header-proxy/
const ALLOWED_METHODS = ['GET', 'POST', 'HEAD', 'OPTIONS'];

function handleError(status, statusText, allowOrigin) {
    return new Response(null, {
        status: status,
        statusText: statusText,
        headers: allowOrigin === '' ? {} : {
           'Access-Control-Allow-Origin': allowOrigin,
        }
    });
}

function handleErrorRedirect(location, status = 301) {
    return Response.redirect(location, status);
}

// handle preflight requests
// https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
function handleOptions(request, origin) {
    let headers = request.headers;

    if (
        headers.get('Origin') !== null &&
        headers.get('Access-Control-Request-Method') !== null &&
        headers.get('Access-Control-Request-Headers') !== null
    ) {
        // Cloudflare supports the GET, POST, HEAD, and OPTIONS methods from
        // any origin, and allow any header on requests. These headers must be
        // present on all responses to all CORS preflight requests. In
        // practice, this means all responses to OPTIONS requests.
        let responseHeaders = {
            'Access-Control-Allow-Headers': request.headers.get('Access-Control-Request-Headers'),
            'Access-Control-Allow-Methods': ALLOWED_METHODS.join(', '),
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Max-Age': '86400',
        };

        return new Response(null, {
            status: 204,
            statusText: 'No Content',
            headers: responseHeaders,
        });
    } else {
        return new Response(null, {
            status: 204,
            statusText: 'No Content',
            headers: {
                Allow: ALLOWED_METHODS.join(', '),
            },
        });
    }
}

// https://cors-proxy.example.workers.dev/?https://example.com
async function handleRequest(request, origin) {
    const url = new URL(request.url);
    let newUrl = decodeURIComponent(decodeURIComponent(url.search.substring(1)));

    if (newUrl === '') {
        return handleError(400, 'Bad Request', origin);
    }

    let newRequest = new Request(request, {
        redirect: 'follow',
        headers: request.headers,
    });

    let response;
    try {
        response = await fetch(newUrl, newRequest);
        response = new Response(response.body, response);
    } catch (_) {
        return handleError(400, 'Bad Request', origin);
    }

    // https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#access-control-allow-origin
    response.headers.set('Access-Control-Allow-Origin', origin);
    response.headers.append('Vary', 'Origin');
    return response;
}

function isValidOrigin(origin) {
    try {
        let hosts = ALLOWED_HOSTS.split(',').map(host => host.trim());
        let url = new URL(origin).hostname;
        return hosts.includes(url);
    } catch (_) {
        return false;
    }
}

function proxyRequest(event) {
    const request = event.request;
    const origin = request.headers.get('Origin');
    const allowedMethods = ALLOWED_METHODS.filter((m) => m !== 'OPTIONS');

    if (isValidOrigin(origin)) {
        if (request.method === 'OPTIONS') {
            return handleOptions(request, origin);
        } else if (allowedMethods.includes(request.method)) {
            return handleRequest(request, origin);
        } else {
            return handleError(405, 'Method Not Allowed', origin);
        }
    } else {
        // not allowed, no explanation given
        return handleErrorRedirect(REDIRECT_URL);
    }
}

addEventListener('fetch', event => {
    console.log(test);
    event.respondWith(proxyRequest(event));
});
