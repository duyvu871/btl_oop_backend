import { Container, Title, Text, Button, Stack, Paper } from '@mantine/core';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <Container size="md" style={{ width: '100%', maxWidth: 768 }}>
      <Paper shadow="md" p="xl" radius="md" withBorder>
        <Stack gap="md">
          <Title order={1}>Dashboard</Title>

          <div>
            <Text size="lg" fw={600}>Welcome, {user?.email}!</Text>
            <Text c="dimmed" size="sm">
              Account Status: {user?.verified ? '✅ Verified' : '⚠️ Not Verified'}
            </Text>
          </div>

          {!user?.verified && (
            <Text c="orange" size="sm">
              Please verify your email to unlock all features.
            </Text>
          )}

          <div>
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </Stack>
      </Paper>
    </Container>
  );
}

