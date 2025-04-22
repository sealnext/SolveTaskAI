import {
  Body,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Section,
  Text,
} from '@react-email/components';

export default function EmailVerification() {
  return (
    <Html>
      <Head />
      <Body style={main}>
        <Preview>Activate your Sealnext account with this magic link.</Preview>
        <Container style={container}>
          <Img
            src={`https://sealnext.com/static/email_logo_full.png`}
            width={255}
            height={34}
            alt="SEALNEXT"
          />
          <Heading style={heading}>🪄 Your magic link</Heading>
          <Section style={body}>
            <Text style={paragraph}>
              <Link style={link} href="{{ email_verification_link }}">
                👉 Click here to activate your account 👈
              </Link>
            </Text>
            <Text style={paragraph}>
              If you didn't request this, please <b>ignore</b> this email.
            </Text>
          </Section>
          <Text style={paragraph}>
            Best,<br />
            ~ Sealnext Team
          </Text>
          <Hr style={hr} />
          <Img
            src={`https://sealnext.com/static/email_logo.png`}
            width={32}
            height={32}
          />
          <Text style={footer}>SEALNEXT｜sealnext.com</Text>
          <Text style={footer}>
            support@sealnext.com
          </Text>
        </Container>
      </Body>
    </Html>
  );
}

const main = {
  backgroundColor: '#ffffff',
  fontFamily:
    '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif',
};

const container = {
  margin: '0 auto',
  padding: '20px 25px 48px',
  backgroundImage: 'url("/static/raycast-bg.png")',
  backgroundPosition: 'bottom',
  backgroundRepeat: 'no-repeat, no-repeat',
};

const heading = {
  fontSize: '28px',
  fontWeight: 'bold',
  marginTop: '48px',
};

const body = {
  margin: '24px 0',
};

const paragraph = {
  fontSize: '16px',
  lineHeight: '26px',
};

const link = {
  color: '#FF6363',
};

const hr = {
  borderColor: '#dddddd',
  marginTop: '48px',
};

const footer = {
  color: '#8898aa',
  fontSize: '12px',
  marginLeft: '4px',
};
