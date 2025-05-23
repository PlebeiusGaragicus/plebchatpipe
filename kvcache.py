############################################################
# Use this: https://lmcache.ai/kv_cache_calculator.html
############################################################

class KVCache:
    def __init__(
        self,
        num_tokens: int,
        hidden_size: int,
        num_layers: int,
        num_heads: int,
        num_kv_groups: int = None,
        quantization: str = "q8_0",
        model_name: str = "Unknown Model"
    ):
        """
        Initialize the KVCache object with model and inference parameters.
        
        Args:
            num_tokens (int): Number of tokens in the context (input + generated tokens).
            hidden_size (int): Hidden size (d_model) of the transformer model.
            num_layers (int): Number of transformer layers in the model.
            num_heads (int): Number of attention heads in the model (for Query).
            num_kv_groups (int, optional): Number of Key-Value groups for GQA. If None, assumes
                                          standard multi-head attention (num_kv_groups = num_heads).
            quantization (str): Quantization type for the KV cache (e.g., 'q8_0', 'fp16', 'fp32').
                               Default is 'q8_0' (8-bit quantization).
            model_name (str): Name of the model for display purposes. Default is 'Unknown Model'.
        """
        self.num_tokens = num_tokens
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.num_kv_groups = num_kv_groups if num_kv_groups is not None else num_heads
        self.quantization = quantization
        self.model_name = model_name
        
        # Validate quantization type
        if quantization not in ["q8_0", "fp16", "fp32"]:
            raise ValueError(f"Unsupported quantization type: {quantization}")

    def calculate_cache(self) -> float:
        """
        Calculate the size of the KV cache and pretty-print the result.
        
        Returns:
            float: Size of the KV cache in gigabytes (GB).
        """
        # Step 1: Calculate Key/Value size per group (not per head)
        kv_size_per_group = self.hidden_size // self.num_heads  # Size of Key or Value vector per head (same as per group)
        total_kv_size_per_group = kv_size_per_group * 2  # Key + Value per group
        
        # Step 2: Total dimensions per token per layer (across all KV groups, not heads)
        dimensions_per_token_per_layer = total_kv_size_per_group * self.num_kv_groups
        
        # Step 3: Total dimensions per token (across all layers)
        dimensions_per_token = dimensions_per_token_per_layer * self.num_layers
        
        # Step 4: Determine bytes per dimension based on quantization
        bytes_per_dimension = {
            "q8_0": 1,  # 8-bit quantization
            "fp16": 2,  # 16-bit floating point
            "fp32": 4   # 32-bit floating point
        }[self.quantization]
        
        # Step 5: Total bytes for all tokens
        total_bytes = dimensions_per_token * self.num_tokens * bytes_per_dimension
        
        # Step 6: Convert bytes to gigabytes (GB)
        total_gb = total_bytes / (1024 ** 3)  # 1 GB = 1024^3 bytes
        
        # Step 7: Pretty-print the result
        gqa_note = "with GQA" if self.num_kv_groups != self.num_heads else "without GQA"
        print(f"KV Cache Size for {self.num_tokens:,} tokens ({self.model_name}, {self.quantization}, {gqa_note}): {round(total_gb, 2)} GB")
        
        return round(total_gb, 2)


# Example usage for Llama 3.1 models with 10,000 tokens
if __name__ == "__main__":
    # Llama 3.1-8B (no GQA)
    llama_8b = KVCache(
        num_tokens=10000,
        hidden_size=4096,
        num_layers=32,
        num_heads=32,
        num_kv_groups=32,  # Same as num_heads since no GQA
        quantization="q8_0",
        model_name="Llama 3.1-8B"
    )
    llama_8b.calculate_cache()
    
    # Llama 3.1-70B (with GQA)
    llama_70b = KVCache(
        num_tokens=10000,
        hidden_size=8192,
        num_layers=80,
        num_heads=64,
        num_kv_groups=8,  # GQA: 8 KV groups for 64 heads
        quantization="q8_0",
        model_name="Llama 3.1-70B"
    )
    llama_70b.calculate_cache()
    
    # Llama 3.1-405B (with GQA)
    llama_405b = KVCache(
        num_tokens=10000,
        hidden_size=16384,
        num_layers=126,
        num_heads=128,
        num_kv_groups=16,  # GQA: 16 KV groups for 128 heads
        quantization="q8_0",
        model_name="Llama 3.1-405B"
    )
    llama_405b.calculate_cache()
