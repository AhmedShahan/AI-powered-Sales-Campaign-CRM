"""
Compatibility shim for Hugging Face InferenceClient API differences.

Some versions of `huggingface_hub.InferenceClient` expose `post(...)`,
others expose `text_generation(...)` or `generate(...)`. LangChain's
HuggingFaceEndpoint expects `post`. This shim adds a `post` method that
delegates to whichever method is available.

This file is imported early (from workflow/main_workflow.py) before
other modules instantiate HuggingFaceEndpoint.
"""
try:
    from huggingface_hub import InferenceClient

    if not hasattr(InferenceClient, "post"):
        def _hf_post(self, *args, **kwargs):
            """Compatibility wrapper to emulate a `post(url, json=payload)` call.

            LangChain's HuggingFaceEndpoint often calls `client.post(..., json={"inputs":..., "parameters":...})`.
            Map that payload to the available client method.
            """
            # Extract payload from kwargs if provided
            payload = kwargs.get("json") or (args[1] if len(args) > 1 else None) if args else None

            # Determine inputs and parameters
            inputs = None
            parameters = None
            if isinstance(payload, dict):
                inputs = payload.get("inputs") or payload.get("data") or payload.get("prompt")
                parameters = payload.get("parameters") or payload.get("params")

            # Fallback to first positional arg if no payload
            if inputs is None and args:
                inputs = args[0]

            # Try available methods with mapped arguments
            if hasattr(self, "text_generation"):
                # text_generation often expects inputs= and parameters=
                try:
                    return self.text_generation(inputs=inputs, parameters=parameters)
                except TypeError:
                    # fallback to positional
                    return self.text_generation(inputs)
            if hasattr(self, "generate"):
                try:
                    return self.generate(inputs=inputs, parameters=parameters)
                except TypeError:
                    return self.generate(inputs)
            if hasattr(self, "request"):
                return self.request(*args, **kwargs)
            raise AttributeError(
                "InferenceClient has no compatible method (post/text_generation/generate/request)"
            )

        InferenceClient.post = _hf_post

    # Also patch AsyncInferenceClient if available (for async flows)
    try:
        from huggingface_hub import AsyncInferenceClient
        if not hasattr(AsyncInferenceClient, "post"):
            async def _async_hf_post(self, *args, **kwargs):
                payload = kwargs.get("json") or (args[1] if len(args) > 1 else None) if args else None
                inputs = None
                parameters = None
                if isinstance(payload, dict):
                    inputs = payload.get("inputs") or payload.get("data") or payload.get("prompt")
                    parameters = payload.get("parameters") or payload.get("params")
                if inputs is None and args:
                    inputs = args[0]
                if hasattr(self, "text_generation"):
                    try:
                        return await self.text_generation(inputs=inputs, parameters=parameters)
                    except TypeError:
                        return await self.text_generation(inputs)
                if hasattr(self, "generate"):
                    try:
                        return await self.generate(inputs=inputs, parameters=parameters)
                    except TypeError:
                        return await self.generate(inputs)
                if hasattr(self, "request"):
                    return await self.request(*args, **kwargs)
                raise AttributeError(
                    "AsyncInferenceClient has no compatible method (post/text_generation/generate/request)"
                )

            AsyncInferenceClient.post = _async_hf_post
    except Exception:
        pass
except Exception:
    # If huggingface_hub not available or any error, silently skip; runtime
    # will surface the missing dependency later.
    pass
