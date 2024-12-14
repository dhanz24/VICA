import { useState } from "react";
import { BrowserRouter as Router, Outlet, Route, Routes } from 'react-router-dom'

import Home from "./pages/Home";
import Login from "./pages/Auth";
import Signup from "./pages/Signup";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </Router>
  );
}

export default App;
