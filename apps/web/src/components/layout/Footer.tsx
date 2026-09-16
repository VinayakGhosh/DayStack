import { Layers3 } from 'lucide-react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="bg-card border-t border-border py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <Link to="/" className="flex items-center gap-2 text-foreground">
              <Layers3 className="h-8 w-8 text-primary" />
              <span className="text-xl font-bold">DayStack</span>
            </Link>
            <p className="text-muted-foreground text-sm">
              A personal place to turn planned work into completed work.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Product</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/#features" className="text-muted-foreground hover:text-foreground text-sm transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link to="/signup" className="text-muted-foreground hover:text-foreground text-sm transition-colors">
                  Create your DayStack
                </Link>
              </li>
              <li>
                <Link to="/login" className="text-muted-foreground hover:text-foreground text-sm transition-colors">
                  Sign in
                </Link>
              </li>
            </ul>
          </div>

        </div>

        <div className="border-t border-border mt-8 pt-8 text-center text-muted-foreground text-sm">
          <p>&copy; {new Date().getFullYear()} DayStack. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
