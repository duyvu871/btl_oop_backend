import { Container, Alert, Button, Stack, Text } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { useAuth } from '@/hooks/useAuth';
import { useResendVerification } from '@/hooks/useVerification';

export function EmailVerificationBanner() {
  const { user } = useAuth();
  const resendMutation = useResendVerification();

  if (!user || user.verified) {
    return null;
  }

  const handleResend = async () => {
    try {
      await resendMutation.mutateAsync({ email: user.email });
    } catch (error) {
      console.error('Failed to resend verification:', error);
    }
  };

  return (
    <Container size="lg" mt="md">
      <Alert
        icon={<IconAlertCircle size={16} />}
        title="Email Verification Required"
        color="yellow"
        variant="filled"
      >
        <Stack gap="sm">
          <Text size="sm">
            Please verify your email address to access all features. We sent a verification code to{' '}
            <strong>{user.email}</strong>
          </Text>
          <div>
            <Button
              variant="white"
              size="xs"
              onClick={handleResend}
              loading={resendMutation.isPending}
            >
              Resend Verification Email
            </Button>
          </div>
          {resendMutation.isSuccess && (
            <Text size="xs" c="white">
              ✓ Verification code sent! Check your email.
            </Text>
          )}
          {resendMutation.isError && (
            <Text size="xs" c="white">
              ✗ {resendMutation.error instanceof Error && 'response' in resendMutation.error
                ? (resendMutation.error as unknown as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to send verification code'
                : 'Failed to send verification code'}
            </Text>
          )}
        </Stack>
      </Alert>
    </Container>
  );
}
