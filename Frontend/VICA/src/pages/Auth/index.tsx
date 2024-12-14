import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FcGoogle } from "react-icons/fc";
import { userSignin, loginWithGoogle } from "../../services/auth-service";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Handle login with email and password
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      const response = await userSignin(email, password);

      if (response) {
        window.open("http://localhost:8000/chainlit", "_blank");
      }
    } catch (err: any) {
      setError(err.response?.data?.message || "Login failed. Please try again.");
    }
  };

  // Handle Google login
  const handleGoogleLogin = async () => {
    try {
      const response = await loginWithGoogle();

      if (response) {
        window.open("http://localhost:8000/chainlit", "_blank");
      }
    } catch (error) {
      console.error("Google login failed:", error);
      setError("Google login failed. Please try again.");
    }
  };

  return (
    <>
      <div className="hero bg-base-100 min-h-screen">
        <div className="hero-content flex-col lg:flex-row-reverse">
          <div className="card bg-base-100 w-96 max-w-sm shrink-0 shadow-2xl">
            <form className="card-body" onSubmit={handleLogin}>
              {error && (
                <div className="alert alert-error text-white">
                  <span>{error}</span>
                </div>
              )}
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Email</span>
                </label>
                <input
                  type="email"
                  placeholder="email"
                  className="input input-bordered"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Password</span>
                </label>
                <input
                  type="password"
                  placeholder="password"
                  className="input input-bordered"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <label className="label">
                  <a href="#" className="label-text-alt link link-hover">
                    Forgot password?
                  </a>
                </label>
              </div>
              <div className="form-control mt-6">
                <button className="btn btn-neutral" type="submit">
                  Login
                </button>
              </div>
              <div className="form-control">
                <button
                  type="button"
                  className="btn btn-outline btn-neutral"
                  onClick={handleGoogleLogin}
                >
                  <FcGoogle className="size-6" /> Login with Google
                </button>
              </div>
            </form>
            <div className="form-control my-4">
              <p className="text-center">
                Don't have an account?{" "}
                <a href="/signup" className="link link-hover font-bold">
                  Sign up
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;
