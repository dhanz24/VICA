import { Link } from 'react-router-dom';

import logo_telkom from '../../assets/telkom-logo-color.png';
import logo_vica from '../../assets/VICA.png';

const Home = () => {
  return (
    <>
      {/* Navbar */}
      <div className="navbar bg-base-100 sticky top-0 z-50 shadow-md">
        <div className="navbar-start">
          <img src={logo_telkom} alt="Telkom Logo" className="h-16 mr-2 " />
          <a
            className='transition ease-in-out delay-50 hover:scale-110 duration-300 cursor-pointer'
            onClick={() => window.location.reload()}
          >
            <img src={logo_vica} alt='VICA Logo' className='h-6'></img>
          </a>
        </div>
        <div className="navbar-center hidden lg:flex">
          <ul className="menu menu-horizontal px-1">
            <li><a>Home</a></li>
            <li><a>Products</a></li>
            <li><a>About Us</a></li>
          </ul>
        </div>
        <div className="navbar-end">
          <Link to="/login" className="btn">Sign In</Link>
        </div>
      </div>

      {/* Hero Section */}
      <div className="hero bg-base-100 min-h-screen relative overflow-hidden">
        {/* Animated Eclipse */}
        <div className="absolute inset-0 flex justify-center items-center animate-move">
          <div className="w-96 h-96 rounded-full bg-gradient-radial from-red-500 opacity-70 blur-xl animate-pulse"></div>
        </div>

        <div className="hero-content text-center relative z-10">
          <div className="max-w-max">
            <h1 className="text-5xl font-bold tex">
              Empowering Conversations with <br /> Visual Intelligence
            </h1>
            <p className="py-8 text-center">
              VICA is a cutting-edge chatbot that combines advanced AI with visual recognition, designed to enhance interactions by providing intuitive, 
              intelligent responses. Whether you're seeking information, solving problems, or exploring new ideas, VICA seamlessly integrates visual insights 
              and conversational expertise to offer a smarter, more efficient user experience. With its ability to understand and respond to both text and images, 
              VICA is the future of interactive assistant technology, bringing a new level of intelligence to your fingertips.
            </p>
            <Link to="/login"><button className="btn btn-outline">Get Started</button></Link>
          </div>
        </div>
      </div>
    </>
  );
};

export default Home;