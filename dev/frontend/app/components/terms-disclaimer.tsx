import React from 'react';
import { Link } from 'react-router';

export function TermsDisclaimer() {
	return (
		<div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 [&_a]:hover:text-primary  ">
			By clicking continue, you agree to our <Link to="/terms">Terms of Service</Link>{" "}
			and <Link to="/privacy">Privacy Policy</Link>.
		</div>
	);
};