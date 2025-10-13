-- Manual SQL query to insert the failed expert
-- This expert failed to be created due to schema mismatch (first_message column doesn't exist)

INSERT INTO experts (
    id, 
    name, 
    description, 
    system_prompt, 
    voice_id, 
    elevenlabs_agent_id, 
    avatar_url, 
    pinecone_index_name, 
    selected_files, 
    knowledge_base_tool_id, 
    is_active,
    created_at,
    updated_at
) VALUES (
    '5f2cf2f4-185d-4e66-acc0-742127ea968f',
    'chris',
    'yo are a chris an expert of therapist',
    NULL,
    NULL,
    'agent_2001k7ek3n5qea29sfpf8jyvkz2r',
    'https://ai-dilan.s3.us-east-1.amazonaws.com/expert-avatars/20251013_162057_1b4877ac.png',
    'agent_2001k7ek3n5qea29sfpf8jyvkz2r',
    '["1e604360-9ca1-4f1d-89b4-f1dc28853043", "e3d74085-5dca-4f1f-a4c4-2611172c76b7"]'::jsonb,
    'tool_1401k7ek3pbxem7aa9dvqck3ndp0',
    true,
    NOW(),
    NOW()
);

-- Verify the insertion
SELECT * FROM experts WHERE elevenlabs_agent_id = 'agent_2001k7ek3n5qea29sfpf8jyvkz2r';
