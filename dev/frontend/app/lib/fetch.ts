async function myFetch(input: string | URL | Request, init?: RequestInit) {
	const response = await fetch(input, init);
	if (response.ok) {
		return response.json();
	}

	if (response.status === 401) {
		throw new Error("Unauthorized");
	}

	throw new Error(`HTTP error! status: ${response.status}`);
}

export { myFetch };
