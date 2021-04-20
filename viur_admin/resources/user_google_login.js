function onSignIn(googleUser) {
	window.location.href = "/login?token=" + googleUser.getAuthResponse().id_token + "&skey=" + document.querySelector("meta[name='google-signin-client_id']").dataset.skey;
}
