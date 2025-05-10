import { z } from "zod";

export const validatePassword = (password: string): string[] => {
  const errors: string[] = [];

  if (password.length < 12) {
    errors.push("Password must be at least 12 characters long.");
  }

  if (!/[a-zA-Z]/.test(password)) {
    errors.push("Password must contain at least one letter.");
  }

  if (!/\d/.test(password)) {
    errors.push("Password must contain at least one number.");
  }

  if (!/[^a-zA-Z0-9]/.test(password)) {
    errors.push("Password must contain at least one symbol.");
  }

  return errors;
};

const passwordSchema = z.string()
  .refine(
    password => validatePassword(password).length === 0,
    {
      message: "Password doesn't meet requirements"
    }
  );

export const emailSchema = z.string().email();

export const loginSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
});

export const userSchema = z.object({
  name: z.string().nullable(),
  email: z.string().email(),
  isEmailVerified: z.boolean(),
});

// Type exports
export type Password = z.infer<typeof passwordSchema>;
export type Email = z.infer<typeof emailSchema>;
export type Login = z.infer<typeof loginSchema>;
export type User = z.infer<typeof userSchema>;
