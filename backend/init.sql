-- Initialize database with sample data

-- Create sample providers
INSERT INTO providers (id, name, display_name, api_endpoint, is_active, rate_limit_per_minute, timeout_seconds, configuration) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'provider_a', 'Provider A', 'https://api.provider-a.com/verify', true, 60, 30, '{"retry_count": 3, "timeout": 30}'),
('550e8400-e29b-41d4-a716-446655440002', 'provider_b', 'Provider B', 'https://api.provider-b.com/verify', true, 100, 25, '{"retry_count": 2, "timeout": 25}'),
('550e8400-e29b-41d4-a716-446655440003', 'provider_c', 'Provider C', 'https://api.provider-c.com/verify', true, 50, 35, '{"retry_count": 3, "timeout": 35}');

-- Create sample policies (for testing)
INSERT INTO policies (id, member_id, policy_number, coverage_status, expiry_date, source, verified_at) VALUES
('660e8400-e29b-41d4-a716-446655440001', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'POL123456789', 'active', '2024-12-31 23:59:59+00', 'provider', NOW()),
('660e8400-e29b-41d4-a716-446655440002', 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1', 'POL987654321', 'active', '2024-11-30 23:59:59+00', 'provider', NOW()),
('660e8400-e29b-41d4-a716-446655440003', 'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2', 'POL456789123', 'expired', '2023-12-31 23:59:59+00', 'provider', NOW());
