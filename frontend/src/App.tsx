import { Container, Title, Text, Button, Stack } from '@mantine/core';
import { useAuth } from './hooks/useAuth';

function App() {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Container size="sm" mt="xl">
        <Text>Loading...</Text>
      </Container>
    );
  }

  return (
    <Container size="sm" mt="xl">
      <Stack gap="md">
        <Title order={1}>Welcome to Mantine v8 + React Query + Jotai</Title>

        {isAuthenticated ? (
          <>
            <Text size="lg">Hello, {user?.email}!</Text>
            <Text c="dimmed">You are authenticated</Text>
          </>
        ) : (
          <>
            <Text size="lg">You are not authenticated</Text>
            <Button variant="filled">Login</Button>
          </>
        )}

        <Text c="dimmed" size="sm">
          Edit <code>src/App.tsx</code> to get started
        </Text>
      </Stack>
    </Container>
  );
}

export default App;
