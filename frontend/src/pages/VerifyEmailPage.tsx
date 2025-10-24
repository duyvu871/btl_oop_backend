import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  PinInput,
  Button,
  Stack,
  Group,
  Alert,
} from '@mantine/core';
import { IconCheck, IconX, IconMail } from '@tabler/icons-react';
import { useVerifyEmail, useResendVerification } from '@/hooks/useVerification';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  // const navigate = useNavigate();
  const email = searchParams.get('email') || '';
  const codeFromUrl = searchParams.get('code') || '';

  const [code, setCode] = useState(codeFromUrl);

  const verifyMutation = useVerifyEmail();
  const resendMutation = useResendVerification();

  // Auto-submit if code is provided in URL (from email click)
  useEffect(() => {
    if (codeFromUrl && codeFromUrl.length === 6 && email) {
      handleVerify().then(_ => {});
    }
  }, []); // Only run once on mount

  const handleVerify = async () => {
    if (code.length !== 6) return;

    try {
      const result = await verifyMutation.mutateAsync({
        email,
        code,
      });

      if (result.success) {
        // Redirect to login or dashboard
        // setTimeout(() => {
        //   // navigate('/login');
        // }, 2000);
      }
    } catch (error: any) {
      console.error('Verification failed:', error);
    }
  };

  const handleResend = async () => {
    try {
      await resendMutation.mutateAsync({ email });
      setCode(''); // Clear the input
    } catch (error: any) {
      console.error('Resend failed:', error);
    }
  };

  const isLoading = verifyMutation.isPending;
  const isResending = resendMutation.isPending;

  return (
    <Container size="xs" style={{ width: '100%', maxWidth: 420 }}>
      <Paper shadow="md" p="xl" radius="md" withBorder>
        <Stack gap="lg">
          <div style={{ textAlign: 'center' }}>
            <IconMail size={48} style={{ margin: '0 auto' }} />
            <Title order={2} mt="md">Verify Your Email</Title>
            <Text c="dimmed" size="sm" mt="xs">
              We sent a verification code to
            </Text>
            <Text fw={600} size="sm">
              {email}
            </Text>
          </div>

          {verifyMutation.isSuccess && (
            <Alert icon={<IconCheck size={16} />} color="green" title="Success!">
              Email verified successfully! You can now log in.
            </Alert>
          )}

          {verifyMutation.isError && (
            <Alert icon={<IconX size={16} />} color="red" title="Verification Failed">
              {(verifyMutation.error as any)?.response?.data?.detail || 'Invalid or expired code. Please try again.'}
            </Alert>
          )}

          {resendMutation.isSuccess && (
            <Alert icon={<IconCheck size={16} />} color="blue" title="Code Sent">
              A new verification code has been sent to your email.
            </Alert>
          )}

          {resendMutation.isError && (
            <Alert icon={<IconX size={16} />} color="red" title="Failed to Send">
              {(resendMutation.error as any)?.response?.data?.detail || 'Failed to resend verification code.'}
            </Alert>
          )}

          <Stack gap="md" align="center">
            <Text size="sm" c="dimmed">
              Enter the 6-digit code
            </Text>
            <PinInput
              length={6}
              value={code}
              onChange={setCode}
              size="lg"
              type="number"
              disabled={isLoading || verifyMutation.isSuccess}
              onComplete={handleVerify}
            />
          </Stack>

          <Button
            fullWidth
            onClick={handleVerify}
            disabled={code.length !== 6 || isLoading || verifyMutation.isSuccess}
            loading={isLoading}
          >
            {isLoading ? 'Verifying...' : 'Verify Email'}
          </Button>

          <Group justify="center" gap="xs">
            <Text size="sm" c="dimmed">
              Didn't receive the code?
            </Text>
            <Button
              variant="subtle"
              size="sm"
              onClick={handleResend}
              disabled={isResending || verifyMutation.isSuccess}
              loading={isResending}
            >
              Resend Code
            </Button>
          </Group>
        </Stack>
      </Paper>
    </Container>
  );
}

