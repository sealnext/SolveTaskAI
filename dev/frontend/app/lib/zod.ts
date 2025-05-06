import { z } from "zod";

// Password validation (matches Password DTO in Python)
const passwordSchema = z.string()
  .min(12, "Password must be at least 12 characters long.")
  .refine(
    password => /[a-zA-Z]/.test(password),
    "Password must contain at least one letter."
  )
  .refine(
    password => /\d/.test(password),
    "Password must contain at least one number."
  )
  .refine(
    password => /[^a-zA-Z0-9]/.test(password),
    "Password must contain at least one symbol."
  );

export const emailSchema = z.string().email();

export const loginSchema = z.object({
  email: z.string().email(),
  password: passwordSchema,
});

// User schema (matches UserPublic DTO in Python)
export const userSchema = z.object({
  name: z.string().nullable(),
  email: z.string().email(),
  is_email_verified: z.boolean(),
});
