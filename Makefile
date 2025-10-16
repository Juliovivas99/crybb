run:
	python3 src/main.py

test-ai:
	python3 tools/run_ai_smoke.py --pfp-url https://pbs.twimg.com/profile_images/1354481591171891202/Pl0n4YkU.jpg

dev:
	uvicorn src.server:app --host 0.0.0.0 --port $$PORT --reload

test:
	SKIP_CONFIG_VALIDATION=1 python3 -m pytest -q

install:
	pip3 install -r requirements.txt

setup:
	cp env.example .env
	@echo "Please edit .env file with your Twitter API credentials"

clean:
	rm -rf .data/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

diagnose:
	python tools/run_diagnostics.py --mode auto

test-api:
	python3 tools/test_basic_plan.py

stress-test:
	python3 tools/run_stress_test.py

stress-test-custom:
	python3 tools/stress_test_verification.py
