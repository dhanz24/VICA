import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { userSignup } from "../../services/auth-service";

const Signup = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const navigate = useNavigate();

  // Handle signup dengan email dan password
  const handleSignup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
        const response = await userSignup(name, email, password);
        if (response) {
            setSuccess("Signup successful! Redirecting...");
            setTimeout(() => navigate("/login"), 3000);
        }
    } catch (err: any) {
        setError(err.response?.data?.message || "Signup failed. Please try again.");
    }
};

  return (
    <>
      <div className="hero bg-base-100 min-h-screen">
        <div className="hero-content flex-col lg:flex-row-reverse">
          <div className="card bg-base-100 w-96 max-w-sm shrink-0 shadow-2xl">
            <form className="card-body" onSubmit={handleSignup}>
              {error && (
                <div className="alert alert-error text-white">
                  <span>{error}</span>
                </div>
              )}
              {success && (
                <div className="alert alert-success text-white">
                  <span>{success}</span>
                </div>
              )}
              <div className="form-control">
                <label className="label">
                    <span className="label-text">Name</span>
                </label>
                <input
                    type="text"
                    placeholder="Full Name"
                    className="input input-bordered"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
              </div>
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
              </div>
              <div className="form-control mt-6">
                <button className="btn btn-neutral" type="submit">
                  Sign Up
                </button>
              </div>
            </form>
            <div className="form-control my-4">
              <p className="text-center">
                Already have an account?{" "}
                <a
                  href="/login"
                  className="link link-hover font-bold rotate-on-hover"
                >
                  Login
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Signup;
