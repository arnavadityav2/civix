DO $$
DECLARE
  v_user_id uuid;
BEGIN
  -- Create a user
  INSERT INTO civix.civix_user(user_id, external_auth_id, username, display_name, role)
  VALUES (gen_random_uuid(), 'auth1', 'testuser1', 'Test User', 'INVESTIGATOR')
  RETURNING user_id INTO v_user_id;

  -- Set context to civix_api and set current user
  SET ROLE civix_api;
  PERFORM set_config('civix.current_user_id', v_user_id::text, true);

  -- Attempt CTE insert
  WITH new_case AS (
      INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction)
      VALUES (gen_random_uuid(), 'TEST-100', 'Test Case', 'CRIMINAL', 'Test Jur')
      RETURNING case_id
  )
  INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by)
  SELECT case_id, current_setting('civix.current_user_id')::uuid, 'ADMIN', current_setting('civix.current_user_id')::uuid
  FROM new_case;

  -- Verify it was inserted
  IF EXISTS (SELECT 1 FROM civix.investigative_case WHERE case_number = 'TEST-100') THEN
      RAISE NOTICE 'SUCCESS';
  ELSE
      RAISE NOTICE 'FAILED TO FIND CASE';
  END IF;

  -- Clean up
  RESET ROLE;
  DELETE FROM civix.case_access WHERE case_id IN (SELECT case_id FROM civix.investigative_case WHERE case_number = 'TEST-100');
  DELETE FROM civix.investigative_case WHERE case_number = 'TEST-100';
  DELETE FROM civix.civix_user WHERE user_id = v_user_id;
END;
$$;
