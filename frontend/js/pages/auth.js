

const AuthPage = (() => {

  document.getElementById("go-register").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("page-login").classList.remove("active");
    document.getElementById("page-register").classList.add("active");
  });

  document.getElementById("go-login").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("page-register").classList.remove("active");
    document.getElementById("page-login").classList.add("active");
  });

  document.getElementById("form-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form  = e.currentTarget;
    const email = document.getElementById("login-email").value.trim();
    const pass  = document.getElementById("login-password").value;

    UI.clearErrors(form);

    let valid = true;
    if (!email) { UI.showError("login-email", "Введіть email"); valid = false; }
    if (!pass)  { UI.showError("login-password", "Введіть пароль"); valid = false; }
    if (!valid) { return undefined; }

    UI.setLoading(form, true);
    try {
      const tokens = await Api.login(email, pass);
      Store.setAuth(tokens);
      const user = await Api.getMe();
      Store.setUser(user);
      App.showApp();
    } catch (err) {
      UI.showAlert("login-error", err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

  document.getElementById("form-register").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form  = e.currentTarget;
    const email = document.getElementById("reg-email").value.trim();
    const phone = document.getElementById("reg-phone").value.trim();
    const pass  = document.getElementById("reg-password").value;

    UI.clearErrors(form);

    let valid = true;
    if (!email) { UI.showError("reg-email", "Введіть email"); valid = false; }
    if (!/^\+380\d{9}$/.test(phone)) { UI.showError("reg-phone", "Формат: +380XXXXXXXXX"); valid = false; }
    if (pass.length < 8) { UI.showError("reg-password", "Мінімум 8 символів"); valid = false; }
    if (!valid) { return undefined; }

    UI.setLoading(form, true);
    UI.hideAlert("reg-error");
    UI.hideAlert("reg-success");
    try {
      await Api.register({ email, phone, password: pass });
      UI.showAlert("reg-success", "Акаунт створено! Тепер увійдіть у систему.");
      form.reset();
      setTimeout(() => {
        document.getElementById("page-register").classList.remove("active");
        document.getElementById("page-login").classList.add("active");
      }, 1800);
    } catch (err) {
      UI.showAlert("reg-error", err.message);
    } finally {
      UI.setLoading(form, false);
    }
  });

})();
