import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  TextInput,
  PasswordInput,
  Button,
  Stack,
  Alert,
  Anchor,
} from '@mantine/core';
import { IconX } from '@tabler/icons-react';
import { useAuth } from '@/hooks/useAuth';

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoginLoading, loginError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await login({ email, password });
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <Container size="xs" style={{ width: '100%', maxWidth: 420 }}>
      <Paper shadow="md" p="xl" radius="md" withBorder>
        <Stack gap="lg">
          <div>
            <Title order={2}>Login</Title>
            <Text c="dimmed" size="sm" mt="xs">
              Welcome back! Please login to your account
            </Text>
          </div>

          {loginError && (
            <Alert icon={<IconX size={16} />} color="red" title="Login Failed">
              {(loginError as any)?.response?.data?.detail || 'Invalid email or password'}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack gap="md">
              <TextInput
                label="Email"
                placeholder="your@email.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <PasswordInput
                label="Password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <Button type="submit" fullWidth loading={isLoginLoading}>
                Login
              </Button>
            </Stack>
          </form>

          <Text size="sm" ta="center">
            Don't have an account?{' '}
            <Anchor component={Link} to="/register">
              Register
            </Anchor>
          </Text>
        </Stack>
      </Paper>
    </Container>
  );
}

